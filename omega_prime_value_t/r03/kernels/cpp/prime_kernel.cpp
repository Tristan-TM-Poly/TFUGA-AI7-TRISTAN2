#include <algorithm>
#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

using u64 = std::uint64_t;
using u128 = unsigned __int128;

static constexpr u64 MOD = 998244353ULL;
static constexpr u64 ROOT = 3ULL;

u64 mul_mod(u64 a, u64 b, u64 mod) {
    return static_cast<u64>((static_cast<u128>(a) * b) % mod);
}

u64 pow_mod(u64 base, u64 exp, u64 mod) {
    u64 result = 1 % mod;
    base %= mod;
    while (exp) {
        if (exp & 1ULL) result = mul_mod(result, base, mod);
        base = mul_mod(base, base, mod);
        exp >>= 1ULL;
    }
    return result;
}

bool sprp(u64 n, u64 a) {
    if (a % n == 0) return true;
    u64 d = n - 1;
    unsigned s = 0;
    while ((d & 1ULL) == 0) { d >>= 1ULL; ++s; }
    u64 x = pow_mod(a, d, n);
    if (x == 1 || x == n - 1) return true;
    for (unsigned r = 1; r < s; ++r) {
        x = mul_mod(x, x, n);
        if (x == n - 1) return true;
    }
    return false;
}

bool is_prime(u64 n) {
    if (n < 2) return false;
    const u64 small[] = {2,3,5,7,11,13,17,19,23,29,31,37};
    for (u64 p : small) {
        if (n == p) return true;
        if (n % p == 0) return false;
    }
    const u64 bases[] = {2,325,9375,28178,450775,9780504,1795265022};
    for (u64 a : bases) if (!sprp(n, a)) return false;
    return true;
}

std::vector<u64> ntt(std::vector<u64> a, bool invert) {
    const std::size_t n = a.size();
    for (std::size_t i = 1, j = 0; i < n; ++i) {
        std::size_t bit = n >> 1;
        for (; j & bit; bit >>= 1) j ^= bit;
        j ^= bit;
        if (i < j) std::swap(a[i], a[j]);
    }
    for (std::size_t len = 2; len <= n; len <<= 1) {
        u64 wlen = pow_mod(ROOT, (MOD - 1) / len, MOD);
        if (invert) wlen = pow_mod(wlen, MOD - 2, MOD);
        for (std::size_t i = 0; i < n; i += len) {
            u64 w = 1;
            for (std::size_t j = 0; j < len / 2; ++j) {
                u64 u = a[i + j];
                u64 v = mul_mod(a[i + j + len / 2], w, MOD);
                a[i + j] = (u + v) % MOD;
                a[i + j + len / 2] = (u + MOD - v) % MOD;
                w = mul_mod(w, wlen, MOD);
            }
        }
    }
    if (invert) {
        u64 inv_n = pow_mod(static_cast<u64>(n), MOD - 2, MOD);
        for (u64 &x : a) x = mul_mod(x, inv_n, MOD);
    }
    return a;
}

std::vector<u64> convolution(const std::vector<u64>& left, const std::vector<u64>& right) {
    std::size_t needed = left.size() + right.size() - 1;
    std::size_t n = 1;
    while (n < needed) n <<= 1;
    std::vector<u64> a(n), b(n);
    std::copy(left.begin(), left.end(), a.begin());
    std::copy(right.begin(), right.end(), b.begin());
    a = ntt(a, false);
    b = ntt(b, false);
    for (std::size_t i = 0; i < n; ++i) a[i] = mul_mod(a[i], b[i], MOD);
    a = ntt(a, true);
    a.resize(needed);
    return a;
}

int main() {
    const std::vector<u64> values = {
        2ULL, 3ULL, 5ULL, 17ULL, 97ULL, 998244353ULL,
        18446744073709551557ULL, 0ULL, 1ULL, 4ULL, 9ULL, 341ULL, 561ULL,
        18446744073709551615ULL
    };
    const std::vector<u64> left = {1,2,3,4,5};
    const std::vector<u64> right = {7,11,13};
    auto conv = convolution(left, right);
    std::cout << "{\"convolution\":[";
    for (std::size_t i = 0; i < conv.size(); ++i) {
        if (i) std::cout << ',';
        std::cout << conv[i];
    }
    std::cout << "],\"mod_pow\":" << pow_mod(123456789ULL, 12345ULL, MOD) << ",\"primality\":{";
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i) std::cout << ',';
        std::cout << '\"' << values[i] << "\":" << (is_prime(values[i]) ? "true" : "false");
    }
    std::cout << "}}\n";
    return 0;
}
