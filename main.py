#  Copyright 2026 Philterd, LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import math
import json
import argparse
import csv
import os
import sys
import opendp.prelude as dp
from pymongo import MongoClient

# Enable OpenDP features for 2026 stability
dp.enable_features("contrib")

class PhilterDiffuse:
    """
    Differential Privacy Engine for MongoDB.
    Provides mathematical guarantees for PII count aggregations.
    """

    def __init__(self, mongo_uri=None, collection_name=None):
        if mongo_uri:
            self.client = MongoClient(mongo_uri)
            # MongoDB URI format: mongodb://host:port/database
            # We'll parse the database from the URI path
            import urllib.parse
            parsed = urllib.parse.urlparse(mongo_uri)
            db_name = parsed.path.strip('/')
            
            if not db_name:
                # Fallback to default if not specified in URI
                db_name = "philter"
            
            self.db = self.client[db_name]
            self.collection_name = collection_name or "pii_counts"
            self.collection = self.db[self.collection_name]
            self.metadata_collection = self.db["privacy_metadata"]
        else:
            self.client = None
            self.collection_name = collection_name or "json_file" # Default label for JSON mode
            self.budget_file = "privacy_budget.json"
        self.sensitivity = 1  # Standard for count-based individual records

    def _get_spent_epsilon(self):
        """
        Retrieves the total epsilon spent for the current collection.
        """
        if self.client:
            record = self.metadata_collection.find_one({"collection": self.collection_name})
            return record.get("spent_epsilon", 0.0) if record else 0.0
        else:
            if os.path.exists(self.budget_file):
                with open(self.budget_file, 'r') as f:
                    budget_data = json.load(f)
                    return budget_data.get(self.collection_name, 0.0)
            return 0.0

    def _update_spent_epsilon(self, new_total):
        """
        Updates the total epsilon spent for the current collection.
        """
        if self.client:
            self.metadata_collection.update_one(
                {"collection": self.collection_name},
                {"$set": {"spent_epsilon": new_total}},
                upsert=True
            )
        else:
            budget_data = {}
            if os.path.exists(self.budget_file):
                with open(self.budget_file, 'r') as f:
                    budget_data = json.load(f)
            budget_data[self.collection_name] = new_total
            with open(self.budget_file, 'w') as f:
                json.dump(budget_data, f)

    def fetch_pii_counts(self, pii_fields):
        """
        Fetches raw counts for specific PII types from MongoDB.
        In a production scenario, this replaces manual count logic.
        """
        if not self.client:
            raise ValueError("MongoDB client not initialized. Cannot fetch counts from database.")

        raw_counts = {}
        for field in pii_fields:
            # Simple count of documents where the PII field exists
            count = self.collection.count_documents({field: {"$exists": True}})
            raw_counts[field] = count
        return raw_counts

    def load_counts_from_json(self, file_path):
        """
        Loads raw counts from a JSON file.
        """
        with open(file_path, 'r') as f:
            return json.load(f)

    def write_counts_to_csv(self, private_counts, file_path, threshold=0):
        """
        Writes privatized counts to a CSV file.
        """
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['PII Type', 'Private Count'])
            for key, value in private_counts.items():
                # Ensure counts don't display as negative
                safe_count = max(0, value)
                
                # Apply threshold
                display_count = "None" if safe_count < threshold else safe_count
                
                writer.writerow([key, display_count])

    def privatize_counts(self, raw_counts, scale=2.0, budget_ceiling=10.0):
        """
        Applies Discrete Laplace noise to counts and calculates Epsilon.
        Checks against a persistent budget ceiling.
        """
        # 1. Calculate Epsilon for this query
        if scale <= 0:
            raise ValueError("Scale must be a positive number.")
            
        epsilon_this_query = self.sensitivity / scale
        
        # 2. Check Budget
        spent_epsilon = self._get_spent_epsilon()
        budget_exhausted = False
        if (spent_epsilon + epsilon_this_query) > budget_ceiling:
            # Refuse to execute by using infinite noise
            # Alternatively, we could raise an error, but the prompt says 
            # "refuse to execute or automatically increase the noise (scale) to infinite levels"
            scale = float('inf')
            epsilon_this_query = 0.0
            budget_exhausted = True
            print(f"WARNING: Budget ceiling of {budget_ceiling} exceeded. Infinite noise applied.")

        # 3. Define the Measurement
        if math.isinf(scale):
            # If scale is infinite, all results are just noise, or we can just return 0 
            # but usually infinite noise means we don't return meaningful data.
            # OpenDP make_laplace might handle inf scale, but let's be safe.
            private_results = {k: 0 for k in raw_counts}
        else:
            measurement = dp.m.make_laplace(
                input_domain=dp.atom_domain(T=int),
                input_metric=dp.absolute_distance(T=int),
                scale=float(scale)
            )
            # 4. Privatize and ensure no negative numbers
            # Cast counts to int for OpenDP compatibility (i32)
            private_results = {k: max(0, measurement(int(v))) for k, v in raw_counts.items()}

        # 5. Update Budget if it was a valid query
        if not math.isinf(scale):
            self._update_spent_epsilon(spent_epsilon + epsilon_this_query)

        return private_results, epsilon_this_query, budget_exhausted

    def generate_audit_report(self, raw, private, epsilon, csv_file=None, threshold=0, budget_exhausted=False):
        """
        Outputs a compliance-ready report for auditors.
        """
        print("\n" + "="*40)
        print("PRIVACY AUDIT REPORT")
        print("="*40)
        if budget_exhausted:
            print("!!! WARNING: PRIVACY BUDGET EXHAUSTED !!!")
            print("!!! NO MORE ACCURATE QUERIES ALLOWED !!!")
            print("-" * 40)
        print(f"Privacy Loss (Epsilon): {epsilon:.4f}")
        print(f"Protection Strength:   {self._interpret_epsilon(epsilon)}")
        print(f"Influence Limit:      e^{epsilon:.2f} ({math.exp(epsilon):.2f}x)")
        if csv_file:
            print(f"Output File:          {csv_file}")
        if threshold > 0:
            print(f"Count Threshold:      {threshold}")
        print("-" * 40)
        print(f"{'PII Type':<15} | {'Raw':<8} | {'Private':<8}")
        print("-" * 40)
        for key in raw:
            # Ensure counts don't display as negative
            safe_count = max(0, private[key])
            
            # Apply threshold
            display_count = "None" if safe_count < threshold else safe_count
            
            print(f"{key:<15} | {raw[key]:<8} | {display_count:<8}")
        
        if csv_file:
            print("-" * 40)
            print(f"Results successfully written to {csv_file}")
            
        print("="*40 + "\n")

    def _interpret_epsilon(self, epsilon):
        if epsilon <= 0.1: return "EXTREME"
        if epsilon <= 1.0: return "HIGH"
        if epsilon <= 5.0: return "MODERATE"
        return "LOW (Testing Only)"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Philter Diffuse: Differential Privacy Engine.")
    parser.add_argument("--input", type=str, help="Path to a JSON document containing PII entity counts.")
    parser.add_argument("--mongo-uri", type=str, default="mongodb://localhost:27017/philter", help="MongoDB connection URI (format: mongodb://host:port/database).")
    parser.add_argument("--scale", type=float, default=2.0, help="Scale for Laplace noise (higher = more privacy, less accuracy).")
    parser.add_argument("--output", type=str, required=True, help="Path to write the privatized PII counts to a CSV file.")
    parser.add_argument("--threshold", type=int, default=0, help="Counts below this threshold will be output as 'None'.")
    parser.add_argument("--budget-ceiling", type=float, default=10.0, help="The maximum total epsilon allowed per collection.")
    
    args = parser.parse_args()

    FIELDS_TO_MONITOR = ["creditcard", "ssn", "age", "zipcode"]

    try:
        if args.input:
            # Initialize Engine without MongoDB for JSON mode
            # Use the JSON filename as the collection name for budget tracking
            json_filename = os.path.basename(args.input)
            engine = PhilterDiffuse(collection_name=json_filename)
            print(f"Loading counts from {args.input}...")
            raw_data = engine.load_counts_from_json(args.input)
        else:
            # Initialize Engine with MongoDB
            try:
                engine = PhilterDiffuse(args.mongo_uri)
                # 1. Fetch raw data
                # Attempt to fetch from DB
                raw_data = engine.fetch_pii_counts(FIELDS_TO_MONITOR)
            except Exception as e:
                print(f"Error: MongoDB connection failed: {e}")
                sys.exit(1)

        # 2. Privatize
        private_data, spent_epsilon, exhausted = engine.privatize_counts(raw_data, scale=args.scale, budget_ceiling=args.budget_ceiling)

        # 3. Output to CSV
        engine.write_counts_to_csv(private_data, args.output, threshold=args.threshold)
        
        # 4. Report
        engine.generate_audit_report(raw_data, private_data, spent_epsilon, csv_file=args.output, threshold=args.threshold, budget_exhausted=exhausted)

    except SystemExit:
        # Expected exit from sys.exit(1)
        pass
    except Exception as e:
        print(f"Error: {e}")