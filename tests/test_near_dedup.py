import unittest

from course_project_suite.llm_benchmark.near_dedup import (
    jaccard_similarity,
    near_deduplicate,
)


class NearDedupTests(unittest.TestCase):
    def test_minhash_lsh_identifies_duplicates_and_near_duplicates(self):
        base = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda"
        near = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda updated"
        different = "weather finance poetry parsing matrix factorization unrelated words"
        result = near_deduplicate(
            [base, near, different],
            method="minhash_lsh",
            threshold=0.70,
            num_perm=64,
            num_bands=16,
            seed=7,
        )
        self.assertEqual(result.documents, [base, different])
        self.assertEqual(result.removed, 1)
        self.assertEqual(result.clusters[0]["method"], "minhash_lsh")

    def test_minhash_lsh_is_seed_stable(self):
        documents = [
            "one two three four five six seven eight",
            "one two three four five six seven eight nine",
            "completely different content lives here",
        ]
        first = near_deduplicate(documents, method="minhash_lsh", threshold=0.65, seed=13)
        second = near_deduplicate(documents, method="minhash_lsh", threshold=0.65, seed=13)
        self.assertEqual(first.documents, second.documents)
        self.assertEqual(first.clusters, second.clusters)

    def test_jaccard_and_minhash_agree_on_small_obvious_case(self):
        documents = [
            "red green blue yellow orange purple",
            "red green blue yellow orange purple extra",
            "database kernel scheduler compiler linker",
        ]
        jaccard = near_deduplicate(documents, method="jaccard", threshold=0.65)
        minhash = near_deduplicate(documents, method="minhash_lsh", threshold=0.65)
        self.assertEqual(jaccard.documents, minhash.documents)
        self.assertGreater(jaccard_similarity(documents[0], documents[1]), 0.65)

    def test_unknown_method_raises(self):
        with self.assertRaises(ValueError):
            near_deduplicate(["a b c"], method="unknown")


if __name__ == "__main__":
    unittest.main()
