import unittest

from sage_tristan.prime_tensors import (
    finite_prime_tensor_packet,
    gap_tensor,
    modular_gap_tensor,
    overflow,
    prime_coordinate_tensor,
    primes_up_to_count,
    reconstruct_mixed_radix,
    residue_gap_identity_holds,
)


class PrimeTensorTests(unittest.TestCase):
    def test_first_primes(self):
        self.assertEqual(primes_up_to_count(8), [2, 3, 5, 7, 11, 13, 17, 19])

    def test_mixed_radix_reconstruction(self):
        primes = primes_up_to_count(8)
        rows = prime_coordinate_tensor(primes)
        for i, row in enumerate(rows):
            self.assertEqual(
                reconstruct_mixed_radix(row, primes[:i], overflow(primes[i], primes[:i])),
                primes[i],
            )

    def test_known_coordinate_rows(self):
        primes = primes_up_to_count(8)
        rows = prime_coordinate_tensor(primes)
        self.assertEqual(rows[1], [1])
        self.assertEqual(rows[2], [1, 2])
        self.assertEqual(rows[3], [1, 0, 1])

    def test_gap_and_modular_identity(self):
        primes = primes_up_to_count(12)
        self.assertTrue(residue_gap_identity_holds(primes, max_jump=3))
        gaps = gap_tensor(primes, max_jump=1)
        modular = modular_gap_tensor(primes, max_jump=1)
        self.assertEqual(gaps[1][8], [0, 0, 1, 0, 0, 0, 0, 0])
        self.assertEqual(modular[1][8][:3], [0, 0, 1])

    def test_packet_checks_and_nodes(self):
        packet = finite_prime_tensor_packet(10, 2)
        self.assertTrue(packet['checks']['reconstruction'])
        self.assertTrue(packet['checks']['residue_gap_identity'])
        self.assertEqual(packet['nodes'][0]['prime'], 2)
        self.assertEqual(packet['nodes'][1]['oak_status'], 'observed')
        self.assertIn('hyperedges', packet)


if __name__ == '__main__':
    unittest.main()
