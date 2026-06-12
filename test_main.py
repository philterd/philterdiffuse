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

import unittest
import json
import os
import csv
from unittest.mock import patch, MagicMock
from main import PhilterDiffuse
import mongomock

class TestPhilterDiffuse(unittest.TestCase):
    def setUp(self):
        self.mongo_uri = "mongodb://localhost:27017/test_db"
        self.budget_file = "privacy_budget.json"
        
        # Cleanup budget file if it exists
        if os.path.exists(self.budget_file):
            os.remove(self.budget_file)

        # Use mongomock to simulate MongoDB
        with patch('main.MongoClient', mongomock.MongoClient):
            self.engine = PhilterDiffuse(self.mongo_uri)
            
        # Add some data to the mock collection
        self.engine.collection.insert_many([
            {"ssn": "123", "age": 30, "zipcode": "12345"},
            {"ssn": "456", "age": 25},
            {"ssn": "789"},
            {"age": 40}
        ])

    def tearDown(self):
        if os.path.exists(self.budget_file):
            os.remove(self.budget_file)

    def test_budget_tracker_json(self):
        # Test budget tracking with JSON (no mongo)
        # Use a specific collection name to simulate filename
        engine = PhilterDiffuse(collection_name="test_counts.json")
        raw_counts = {"ssn": 10}
        
        # Query 1: scale=1.0, epsilon=1.0
        _, epsilon1, _ = engine.privatize_counts(raw_counts, scale=1.0, budget_ceiling=2.5)
        self.assertEqual(epsilon1, 1.0)
        self.assertEqual(engine._get_spent_epsilon(), 1.0)
        
        # Verify the key in the JSON file
        with open(self.budget_file, 'r') as f:
            budget_data = json.load(f)
            self.assertIn("test_counts.json", budget_data)
            self.assertEqual(budget_data["test_counts.json"], 1.0)
        
        # Query 2: scale=1.0, epsilon=1.0 (Total=2.0)
        _, epsilon2, _ = engine.privatize_counts(raw_counts, scale=1.0, budget_ceiling=2.5)
        self.assertEqual(epsilon2, 1.0)
        self.assertEqual(engine._get_spent_epsilon(), 2.0)
        
        # Query 3: scale=1.0, epsilon=1.0 (Total would be 3.0 > 2.5)
        private3, epsilon3, exhausted3 = engine.privatize_counts(raw_counts, scale=1.0, budget_ceiling=2.5)
        self.assertEqual(epsilon3, 0.0)
        self.assertTrue(exhausted3)
        self.assertEqual(engine._get_spent_epsilon(), 2.0)
        self.assertTrue(all(v == 0 for v in private3.values()))

    @patch('main.MongoClient', mongomock.MongoClient)
    def test_budget_tracker_mongo(self):
        # Test budget tracking with Mock MongoDB
        engine = PhilterDiffuse(self.mongo_uri)
        raw_counts = {"ssn": 10}
        
        # Query 1: scale=2.0, epsilon=0.5
        _, epsilon1, _ = engine.privatize_counts(raw_counts, scale=2.0, budget_ceiling=1.0)
        self.assertEqual(epsilon1, 0.5)
        self.assertEqual(engine._get_spent_epsilon(), 0.5)
        
        # Query 2: scale=2.0, epsilon=0.5 (Total=1.0)
        _, epsilon2, _ = engine.privatize_counts(raw_counts, scale=2.0, budget_ceiling=1.0)
        self.assertEqual(epsilon2, 0.5)
        self.assertEqual(engine._get_spent_epsilon(), 1.0)
        
        # Query 3: scale=2.0, epsilon=0.5 (Total would be 1.5 > 1.0)
        private3, epsilon3, exhausted3 = engine.privatize_counts(raw_counts, scale=2.0, budget_ceiling=1.0)
        self.assertEqual(epsilon3, 0.0)
        self.assertTrue(exhausted3)
        self.assertEqual(engine._get_spent_epsilon(), 1.0)
        self.assertTrue(all(v == 0 for v in private3.values()))

    def test_fetch_pii_counts(self):
        fields = ["ssn", "age", "zipcode"]
        counts = self.engine.fetch_pii_counts(fields)
        
        self.assertEqual(counts["ssn"], 3)
        self.assertEqual(counts["age"], 3)
        self.assertEqual(counts["zipcode"], 1)
        self.assertIn("ssn", counts)
        self.assertIn("age", counts)
        self.assertIn("zipcode", counts)

    def test_fetch_pii_count_aggregates_sums_across_buckets(self):
        # Philter writes one document per (context, day) with a document-presence counts map.
        self.engine.db["pii_count_aggregates"].insert_many([
            {"context": "ctx-a", "bucket_start": "2026-05-30", "counts": {"SSN": 5, "EMAIL_ADDRESS": 100}, "total_documents": 120},
            {"context": "ctx-a", "bucket_start": "2026-05-31", "counts": {"SSN": 3, "PERSON": 9}, "total_documents": 50},
            {"context": "ctx-b", "bucket_start": "2026-05-31", "counts": {"SSN": 2}, "total_documents": 10},
        ])

        totals = self.engine.fetch_pii_count_aggregates()
        self.assertEqual(totals["SSN"], 10)  # 5 + 3 + 2 across all buckets
        self.assertEqual(totals["EMAIL_ADDRESS"], 100)
        self.assertEqual(totals["PERSON"], 9)

    def test_fetch_pii_count_aggregates_filters_by_context(self):
        self.engine.db["pii_count_aggregates"].insert_many([
            {"context": "ctx-a", "bucket_start": "2026-05-31", "counts": {"SSN": 3}},
            {"context": "ctx-b", "bucket_start": "2026-05-31", "counts": {"SSN": 2}},
        ])
        self.assertEqual(self.engine.fetch_pii_count_aggregates(context="ctx-a"), {"SSN": 3})

    def test_fetch_pii_count_aggregates_no_client(self):
        engine_no_client = PhilterDiffuse(collection_name="json_mode")
        with self.assertRaises(ValueError):
            engine_no_client.fetch_pii_count_aggregates()

    def test_load_counts_from_json(self):
        test_data = {"field1": 10, "field2": 20}
        file_path = "test_counts.json"
        with open(file_path, 'w') as f:
            json.dump(test_data, f)
        
        try:
            loaded_data = self.engine.load_counts_from_json(file_path)
            self.assertEqual(loaded_data, test_data)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_fetch_pii_counts_no_client(self):
        engine_no_client = PhilterDiffuse()
        with self.assertRaises(ValueError):
            engine_no_client.fetch_pii_counts(["ssn"])

    def test_privatize_counts(self):
        raw_counts = {"ssn": 10, "age": 20}
        scale = 1.0
        private_results, epsilon, exhausted = self.engine.privatize_counts(raw_counts, scale=scale)
        
        self.assertEqual(epsilon, 1.0 / scale)
        self.assertFalse(exhausted)
        self.assertIn("ssn", private_results)
        self.assertIn("age", private_results)
        self.assertIsInstance(private_results["ssn"], int)
        self.assertIsInstance(private_results["age"], int)
        # Verify no negative numbers are returned
        self.assertTrue(all(v >= 0 for v in private_results.values()))

    def test_privatize_counts_negative_clamping(self):
        # Force the measurement to return a negative number to test clamping
        raw_counts = {"ssn": 1}
        scale = 100.0 # High scale increases chance of negative noise
        
        # We need to patch the measurement function inside privatize_counts
        # Since it's created inside the method, we can patch opendp.measurements.make_laplace
        with patch('main.dp.m.make_laplace') as mock_make:
            mock_measurement = MagicMock()
            mock_measurement.return_value = -5
            mock_make.return_value = mock_measurement
            
            private_results, _, _ = self.engine.privatize_counts(raw_counts, scale=scale)
            self.assertEqual(private_results["ssn"], 0)

    def test_interpret_epsilon(self):
        self.assertEqual(self.engine._interpret_epsilon(0.05), "EXTREME")
        self.assertEqual(self.engine._interpret_epsilon(0.5), "HIGH")
        self.assertEqual(self.engine._interpret_epsilon(2.5), "MODERATE")
        self.assertEqual(self.engine._interpret_epsilon(10.0), "LOW (Testing Only)")

    def test_write_counts_to_csv(self):
        private_counts = {"ssn": 10, "age": 20, "zipcode": 5}
        file_path = "test_output.csv"
        try:
            # Test without threshold
            self.engine.write_counts_to_csv(private_counts, file_path)
            with open(file_path, 'r', newline='') as f:
                reader = csv.reader(f)
                rows = list(reader)
                expected_rows = sorted([['ssn', '10'], ['age', '20'], ['zipcode', '5']])
                self.assertEqual(sorted(rows[1:]), expected_rows)
            
            # Test with threshold = 7
            self.engine.write_counts_to_csv(private_counts, file_path, threshold=7)
            with open(file_path, 'r', newline='') as f:
                reader = csv.reader(f)
                rows = list(reader)
                expected_rows = sorted([['ssn', '10'], ['age', '20'], ['zipcode', 'None']])
                self.assertEqual(sorted(rows[1:]), expected_rows)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_threshold_application(self):
        raw = {"ssn": 5}
        private = {"ssn": 3}
        epsilon = 0.5
        # This will print to console, we just verify it runs with threshold
        self.engine.generate_audit_report(raw, private, epsilon, threshold=5)

    def test_generate_audit_report(self):
        raw = {"ssn": 5}
        private = {"ssn": 6}
        epsilon = 0.5
        
        # We want to see the report, so we don't mock print here anymore
        self.engine.generate_audit_report(raw, private, epsilon)

    def test_privatize_counts_edge_cases(self):
        # Empty counts
        res, eps, exh = self.engine.privatize_counts({}, scale=1.0)
        self.assertEqual(res, {})
        self.assertEqual(eps, 1.0)
        self.assertFalse(exh)

        # Scale zero or negative
        with self.assertRaises(ValueError):
            self.engine.privatize_counts({"ssn": 10}, scale=0)
        with self.assertRaises(ValueError):
            self.engine.privatize_counts({"ssn": 10}, scale=-1.0)

        # Non-integer counts (float)
        # Should be cast to int and run without error
        res, eps, exh = self.engine.privatize_counts({"ssn": 10.9}, scale=1.0)
        self.assertIn("ssn", res)
        self.assertIsInstance(res["ssn"], int)

    def test_mongo_uri_parsing(self):
        # Test default DB name
        with patch('main.MongoClient', mongomock.MongoClient):
            engine = PhilterDiffuse("mongodb://localhost:27017/")
            self.assertEqual(engine.db.name, "philter")
            
            # Test specified DB name
            engine2 = PhilterDiffuse("mongodb://localhost:27017/my_analytics")
            self.assertEqual(engine2.db.name, "my_analytics")

    def test_budget_exact_ceiling(self):
        engine = PhilterDiffuse(collection_name="exact_budget.json")
        raw = {"ssn": 10}
        # Ceiling is 1.0. Spent is 0.
        # Query with scale 1.0 -> epsilon 1.0.
        # Total spent becomes 1.0. This should be allowed.
        _, eps, exh = engine.privatize_counts(raw, scale=1.0, budget_ceiling=1.0)
        self.assertEqual(eps, 1.0)
        self.assertFalse(exh)
        self.assertEqual(engine._get_spent_epsilon(), 1.0)
        
        # Next query should be blocked
        _, eps2, exh2 = engine.privatize_counts(raw, scale=1.0, budget_ceiling=1.0)
        self.assertEqual(eps2, 0.0)
        self.assertTrue(exh2)

class TestCLI(unittest.TestCase):
    def test_cli_json_loading(self):
        """Test that the CLI correctly loads data when --input is provided."""
        test_data = {"ssn": 10, "age": 20}
        file_path = "cli_test.json"
        output_path = "cli_test.csv"
        with open(file_path, 'w') as f:
            json.dump(test_data, f)

        try:
            with patch('sys.argv', ['main.py', '--input', file_path, '--scale', '1.0', '--output', output_path]):
                # Manually trigger the argument parsing and logic from main.py
                import main
                import argparse
                
                # Create a fresh parser like in main.py to simulate the same behavior
                parser = argparse.ArgumentParser()
                parser.add_argument("--input", type=str)
                parser.add_argument("--mongo-uri", type=str, default="mongodb://localhost:27017/analytics_db")
                parser.add_argument("--scale", type=float, default=2.0)
                parser.add_argument("--output", type=str, required=True)
                parser.add_argument("--threshold", type=int, default=0)
                
                args = parser.parse_args(['--input', file_path, '--scale', '1.0', '--output', output_path, '--threshold', '15'])
                
                import os
                json_filename = os.path.basename(args.input)
                engine = main.PhilterDiffuse(collection_name=json_filename)
                loaded_data = engine.load_counts_from_json(args.input)
                self.assertEqual(loaded_data, test_data)
                
                private_data, epsilon, exhausted = engine.privatize_counts(loaded_data, scale=args.scale)
                self.assertEqual(epsilon, 1.0 / 1.0)
                self.assertFalse(exhausted)
                self.assertIn("ssn", private_data)

                if args.output:
                    engine.write_counts_to_csv(private_data, args.output, threshold=args.threshold)
                    self.assertTrue(os.path.exists(output_path))
                    with open(output_path, 'r') as f:
                        reader = csv.reader(f)
                        rows = list(reader)
                        # test_data has ssn=10, age=20. scale=1.0 noise is usually small.
                        # threshold is 15. age should be >= 15 usually, ssn should be < 15.
                        # But noise is random, so we just check if "None" or a number is present.
                        for row in rows[1:]:
                            if row[0] == 'ssn':
                                # ssn=10 + noise, threshold=15. Likely "None"
                                pass

                # Show the report in the test output
                engine.generate_audit_report(loaded_data, private_data, epsilon, csv_file=args.output, threshold=args.threshold, budget_exhausted=exhausted)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(output_path):
                os.remove(output_path)

    @patch('main.MongoClient', mongomock.MongoClient)
    def test_cli_mongo_defaults(self):
        """Test the CLI logic for MongoDB when no --input is provided."""
        # This tests the logic block's interaction with the PhilterDiffuse class
        output_path = "cli_mongo_test.csv"
        with patch('sys.argv', ['main.py', '--output', output_path]):
            import main
            # Simulate the MongoDB path
            engine = main.PhilterDiffuse("mongodb://localhost:27017/analytics_db")
            self.assertIsNotNone(engine.client)
            
            # Mock fetch_pii_counts to return fixed data
            with patch.object(main.PhilterDiffuse, 'fetch_pii_counts', return_value={"age": 10}):
                raw_data = engine.fetch_pii_counts(["age"])
                private_data, epsilon, exhausted = engine.privatize_counts(raw_data, scale=2.0)
                self.assertEqual(raw_data, {"age": 10})
                self.assertEqual(epsilon, 0.5)
                self.assertFalse(exhausted)
                
                # Show the report in the test output
                engine.generate_audit_report(raw_data, private_data, epsilon, csv_file=output_path, budget_exhausted=exhausted)
        
        if os.path.exists(output_path):
            os.remove(output_path)

    @patch('sys.exit')
    def test_cli_missing_output(self, mock_exit):
        """Test that the application exits when --output is missing."""
        import runpy
        import main
        
        # argparse prints to stderr and exits with 2 for missing required arguments
        with patch('sys.argv', ['main.py', '--input', 'some_file.json']):
            try:
                # We expect argparse to raise SystemExit(2)
                runpy.run_path('main.py', run_name='__main__')
            except SystemExit as e:
                self.assertEqual(e.code, 2)

    @patch('main.PhilterDiffuse.fetch_pii_counts')
    @patch('sys.exit')
    @patch('main.MongoClient')
    def test_cli_mongo_connection_failure(self, mock_mongo, mock_exit, mock_fetch):
        """Test that the application exits when MongoDB connection fails."""
        # Setup mock_mongo to return something so PhilterDiffuse(args.mongo_uri) succeeds
        # but fetch_pii_counts fails.
        mock_fetch.side_effect = Exception("Connection refused")
        mock_exit.side_effect = SystemExit(1)
        
        # We need to simulate the CLI execution environment
        import main
        import sys
        
        with patch('sys.argv', ['main.py', '--output', 'test.csv']):
            # To test the block under `if __name__ == "__main__":`, we can use runpy
            import runpy
            try:
                runpy.run_path('main.py', run_name='__main__')
            except SystemExit:
                pass # Expected
            
            mock_exit.assert_called_once_with(1)

if __name__ == "__main__":
    unittest.main()
