use std::slice;

unsafe fn slices2<'a>(x: *const f64, y: *const f64, n: usize) -> Option<(&'a [f64], &'a [f64])> {
    if n > 0 && (x.is_null() || y.is_null()) { return None; }
    Some((slice::from_raw_parts(x, n), slice::from_raw_parts(y, n)))
}

#[no_mangle]
pub unsafe extern "C" fn omega_affine_scalar_f64(x: *const f64, y: *const f64, scalar: f64, out: *mut f64, n: usize) -> i32 {
    if n > 0 && out.is_null() { return 1; }
    let Some((xs, ys)) = slices2(x, y, n) else { return 1; };
    let os = slice::from_raw_parts_mut(out, n);
    for i in 0..n { os[i] = scalar * xs[i] + ys[i]; }
    0
}

#[no_mangle]
pub unsafe extern "C" fn omega_affine_unrolled4_f64(x: *const f64, y: *const f64, scalar: f64, out: *mut f64, n: usize) -> i32 {
    omega_affine_scalar_f64(x, y, scalar, out, n)
}

#[no_mangle]
pub unsafe extern "C" fn omega_affine_avx2_f64(x: *const f64, y: *const f64, scalar: f64, out: *mut f64, n: usize) -> i32 {
    omega_affine_scalar_f64(x, y, scalar, out, n)
}

#[no_mangle]
pub unsafe extern "C" fn omega_affine_parallel_f64(x: *const f64, y: *const f64, scalar: f64, out: *mut f64, n: usize) -> i32 {
    omega_affine_scalar_f64(x, y, scalar, out, n)
}

#[no_mangle]
pub unsafe extern "C" fn omega_affine_inplace_f64(x: *mut f64, y: *const f64, scalar: f64, n: usize) -> i32 {
    if n > 0 && (x.is_null() || y.is_null()) { return 1; }
    let xs = slice::from_raw_parts_mut(x, n);
    let ys = slice::from_raw_parts(y, n);
    for i in 0..n { xs[i] = scalar * xs[i] + ys[i]; }
    0
}

#[no_mangle]
pub unsafe extern "C" fn omega_affine_chain_f64(x: *const f64, y: *const f64, z: *const f64, a: f64, b: f64, out: *mut f64, n: usize) -> i32 {
    if n > 0 && (x.is_null() || y.is_null() || z.is_null() || out.is_null()) { return 1; }
    let xs = slice::from_raw_parts(x, n);
    let ys = slice::from_raw_parts(y, n);
    let zs = slice::from_raw_parts(z, n);
    let os = slice::from_raw_parts_mut(out, n);
    for i in 0..n { os[i] = b * (a * xs[i] + ys[i]) + zs[i]; }
    0
}

#[no_mangle]
pub unsafe extern "C" fn omega_triad_f64(x: *const f64, y: *const f64, z: *const f64, a: f64, out: *mut f64, n: usize) -> i32 {
    if n > 0 && (x.is_null() || y.is_null() || z.is_null() || out.is_null()) { return 1; }
    let xs = slice::from_raw_parts(x, n);
    let ys = slice::from_raw_parts(y, n);
    let zs = slice::from_raw_parts(z, n);
    let os = slice::from_raw_parts_mut(out, n);
    for i in 0..n { os[i] = xs[i] + a * ys[i] + zs[i]; }
    0
}

#[no_mangle]
pub unsafe extern "C" fn omega_sum_f64(x: *const f64, n: usize) -> f64 {
    if n > 0 && x.is_null() { return 0.0; }
    slice::from_raw_parts(x, n).iter().copied().sum()
}

#[no_mangle]
pub unsafe extern "C" fn omega_dot_f64(x: *const f64, y: *const f64, n: usize) -> f64 {
    let Some((xs, ys)) = slices2(x, y, n) else { return 0.0; };
    xs.iter().zip(ys).map(|(a,b)| a*b).sum()
}

#[no_mangle]
pub extern "C" fn omega_feature_mask() -> u64 { 0 }

#[no_mangle]
pub unsafe extern "C" fn omega_affine_chain_avx2_f64(x: *const f64, y: *const f64, z: *const f64, a: f64, b: f64, out: *mut f64, n: usize) -> i32 {
    omega_affine_chain_f64(x, y, z, a, b, out, n)
}
#[no_mangle]
pub unsafe extern "C" fn omega_affine_chain_parallel_f64(x: *const f64, y: *const f64, z: *const f64, a: f64, b: f64, out: *mut f64, n: usize) -> i32 {
    omega_affine_chain_f64(x, y, z, a, b, out, n)
}
#[no_mangle]
pub unsafe extern "C" fn omega_sum_avx2_f64(x: *const f64, n: usize) -> f64 { omega_sum_f64(x, n) }
#[no_mangle]
pub unsafe extern "C" fn omega_dot_avx2_f64(x: *const f64, y: *const f64, n: usize) -> f64 { omega_dot_f64(x, y, n) }
#[no_mangle]
pub unsafe extern "C" fn omega_sum_parallel_f64(x: *const f64, n: usize) -> f64 { omega_sum_f64(x, n) }
#[no_mangle]
pub unsafe extern "C" fn omega_dot_parallel_f64(x: *const f64, y: *const f64, n: usize) -> f64 { omega_dot_f64(x, y, n) }
