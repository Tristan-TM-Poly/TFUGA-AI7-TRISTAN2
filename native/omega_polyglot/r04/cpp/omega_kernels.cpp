#include <cstddef>
#include <cstdint>
#if defined(_OPENMP)
#include <omp.h>
#endif
#if defined(__AVX2__)
#include <immintrin.h>
#endif

extern "C" {

int omega_affine_scalar_f64(const double *__restrict x, const double *__restrict y,
                            double scalar, double *__restrict out, std::size_t n) noexcept {
    if (n > 0 && (x == nullptr || y == nullptr || out == nullptr)) return 1;
    for (std::size_t i = 0; i < n; ++i) out[i] = scalar * x[i] + y[i];
    return 0;
}

int omega_affine_unrolled4_f64(const double *__restrict x, const double *__restrict y,
                               double scalar, double *__restrict out, std::size_t n) noexcept {
    if (n > 0 && (x == nullptr || y == nullptr || out == nullptr)) return 1;
    std::size_t i = 0;
    for (; i + 3 < n; i += 4) {
        out[i] = scalar * x[i] + y[i];
        out[i + 1] = scalar * x[i + 1] + y[i + 1];
        out[i + 2] = scalar * x[i + 2] + y[i + 2];
        out[i + 3] = scalar * x[i + 3] + y[i + 3];
    }
    for (; i < n; ++i) out[i] = scalar * x[i] + y[i];
    return 0;
}

int omega_affine_avx2_f64(const double *__restrict x, const double *__restrict y,
                          double scalar, double *__restrict out, std::size_t n) noexcept {
    if (n > 0 && (x == nullptr || y == nullptr || out == nullptr)) return 1;
#if defined(__AVX2__)
    std::size_t i = 0;
    const __m256d s = _mm256_set1_pd(scalar);
    for (; i + 3 < n; i += 4) {
        const __m256d xv = _mm256_loadu_pd(x + i);
        const __m256d yv = _mm256_loadu_pd(y + i);
#if defined(__FMA__)
        const __m256d ov = _mm256_fmadd_pd(s, xv, yv);
#else
        const __m256d ov = _mm256_add_pd(_mm256_mul_pd(s, xv), yv);
#endif
        _mm256_storeu_pd(out + i, ov);
    }
    for (; i < n; ++i) out[i] = scalar * x[i] + y[i];
    return 0;
#else
    return omega_affine_unrolled4_f64(x, y, scalar, out, n);
#endif
}

int omega_affine_parallel_f64(const double *__restrict x, const double *__restrict y,
                              double scalar, double *__restrict out, std::size_t n) noexcept {
    if (n > 0 && (x == nullptr || y == nullptr || out == nullptr)) return 1;
#if defined(_OPENMP)
#pragma omp parallel for schedule(static)
    for (std::ptrdiff_t i = 0; i < static_cast<std::ptrdiff_t>(n); ++i) out[i] = scalar * x[i] + y[i];
#else
    for (std::size_t i = 0; i < n; ++i) out[i] = scalar * x[i] + y[i];
#endif
    return 0;
}

int omega_affine_inplace_f64(double *__restrict x, const double *__restrict y,
                             double scalar, std::size_t n) noexcept {
    if (n > 0 && (x == nullptr || y == nullptr)) return 1;
    for (std::size_t i = 0; i < n; ++i) x[i] = scalar * x[i] + y[i];
    return 0;
}

int omega_affine_chain_f64(const double *__restrict x, const double *__restrict y,
                           const double *__restrict z, double a, double b,
                           double *__restrict out, std::size_t n) noexcept {
    if (n > 0 && (x == nullptr || y == nullptr || z == nullptr || out == nullptr)) return 1;
    for (std::size_t i = 0; i < n; ++i) out[i] = b * (a * x[i] + y[i]) + z[i];
    return 0;
}

int omega_triad_f64(const double *__restrict x, const double *__restrict y,
                    const double *__restrict z, double a,
                    double *__restrict out, std::size_t n) noexcept {
    if (n > 0 && (x == nullptr || y == nullptr || z == nullptr || out == nullptr)) return 1;
    for (std::size_t i = 0; i < n; ++i) out[i] = x[i] + a * y[i] + z[i];
    return 0;
}

double omega_sum_f64(const double *__restrict x, std::size_t n) noexcept {
    if (n > 0 && x == nullptr) return 0.0;
    double total = 0.0;
    for (std::size_t i = 0; i < n; ++i) total += x[i];
    return total;
}

double omega_dot_f64(const double *__restrict x, const double *__restrict y, std::size_t n) noexcept {
    if (n > 0 && (x == nullptr || y == nullptr)) return 0.0;
    double total = 0.0;
    for (std::size_t i = 0; i < n; ++i) total += x[i] * y[i];
    return total;
}

std::uint64_t omega_feature_mask() noexcept {
    std::uint64_t mask = 0;
#if defined(__AVX2__)
    mask |= 1u;
#endif
#if defined(__FMA__)
    mask |= 2u;
#endif
#if defined(_OPENMP)
    mask |= 4u;
#endif
    return mask;
}

int omega_affine_chain_avx2_f64(const double *__restrict x, const double *__restrict y,
                                const double *__restrict z, double a, double b,
                                double *__restrict out, std::size_t n) noexcept {
    if (n > 0 && (x == nullptr || y == nullptr || z == nullptr || out == nullptr)) return 1;
#if defined(__AVX2__)
    std::size_t i = 0;
    const __m256d av = _mm256_set1_pd(a);
    const __m256d bv = _mm256_set1_pd(b);
    for (; i + 3 < n; i += 4) {
        const __m256d xv = _mm256_loadu_pd(x + i);
        const __m256d yv = _mm256_loadu_pd(y + i);
        const __m256d zv = _mm256_loadu_pd(z + i);
#if defined(__FMA__)
        const __m256d first = _mm256_fmadd_pd(av, xv, yv);
        const __m256d result = _mm256_fmadd_pd(bv, first, zv);
#else
        const __m256d first = _mm256_add_pd(_mm256_mul_pd(av, xv), yv);
        const __m256d result = _mm256_add_pd(_mm256_mul_pd(bv, first), zv);
#endif
        _mm256_storeu_pd(out + i, result);
    }
    for (; i < n; ++i) out[i] = b * (a * x[i] + y[i]) + z[i];
    return 0;
#else
    return omega_affine_chain_f64(x, y, z, a, b, out, n);
#endif
}

int omega_affine_chain_parallel_f64(const double *__restrict x, const double *__restrict y,
                                    const double *__restrict z, double a, double b,
                                    double *__restrict out, std::size_t n) noexcept {
    if (n > 0 && (x == nullptr || y == nullptr || z == nullptr || out == nullptr)) return 1;
#if defined(_OPENMP)
#pragma omp parallel for schedule(static)
    for (std::ptrdiff_t i = 0; i < static_cast<std::ptrdiff_t>(n); ++i) out[i] = b * (a * x[i] + y[i]) + z[i];
#else
    for (std::size_t i = 0; i < n; ++i) out[i] = b * (a * x[i] + y[i]) + z[i];
#endif
    return 0;
}

double omega_sum_avx2_f64(const double *__restrict x, std::size_t n) noexcept {
    if (n > 0 && x == nullptr) return 0.0;
#if defined(__AVX2__)
    std::size_t i = 0;
    __m256d acc = _mm256_setzero_pd();
    for (; i + 3 < n; i += 4) acc = _mm256_add_pd(acc, _mm256_loadu_pd(x + i));
    double lanes[4];
    _mm256_storeu_pd(lanes, acc);
    double total = lanes[0] + lanes[1] + lanes[2] + lanes[3];
    for (; i < n; ++i) total += x[i];
    return total;
#else
    return omega_sum_f64(x, n);
#endif
}

double omega_dot_avx2_f64(const double *__restrict x, const double *__restrict y, std::size_t n) noexcept {
    if (n > 0 && (x == nullptr || y == nullptr)) return 0.0;
#if defined(__AVX2__)
    std::size_t i = 0;
    __m256d acc = _mm256_setzero_pd();
    for (; i + 3 < n; i += 4) {
        const __m256d xv = _mm256_loadu_pd(x + i);
        const __m256d yv = _mm256_loadu_pd(y + i);
#if defined(__FMA__)
        acc = _mm256_fmadd_pd(xv, yv, acc);
#else
        acc = _mm256_add_pd(acc, _mm256_mul_pd(xv, yv));
#endif
    }
    double lanes[4];
    _mm256_storeu_pd(lanes, acc);
    double total = lanes[0] + lanes[1] + lanes[2] + lanes[3];
    for (; i < n; ++i) total += x[i] * y[i];
    return total;
#else
    return omega_dot_f64(x, y, n);
#endif
}

double omega_sum_parallel_f64(const double *__restrict x, std::size_t n) noexcept {
    if (n > 0 && x == nullptr) return 0.0;
    double total = 0.0;
#if defined(_OPENMP)
#pragma omp parallel for reduction(+:total) schedule(static)
    for (std::ptrdiff_t i = 0; i < static_cast<std::ptrdiff_t>(n); ++i) total += x[i];
#else
    for (std::size_t i = 0; i < n; ++i) total += x[i];
#endif
    return total;
}

double omega_dot_parallel_f64(const double *__restrict x, const double *__restrict y, std::size_t n) noexcept {
    if (n > 0 && (x == nullptr || y == nullptr)) return 0.0;
    double total = 0.0;
#if defined(_OPENMP)
#pragma omp parallel for reduction(+:total) schedule(static)
    for (std::ptrdiff_t i = 0; i < static_cast<std::ptrdiff_t>(n); ++i) total += x[i] * y[i];
#else
    for (std::size_t i = 0; i < n; ++i) total += x[i] * y[i];
#endif
    return total;
}

}
