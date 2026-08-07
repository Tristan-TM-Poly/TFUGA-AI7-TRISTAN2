#![no_std]

#[no_mangle]
pub unsafe extern "C" fn omega_dot_u64_rust(
    a: *const u64,
    b: *const u64,
    n: u64,
) -> u64 {
    let mut acc = 0u64;
    let mut i = 0u64;
    while i < n {
        let av = *a.add(i as usize);
        let bv = *b.add(i as usize);
        acc = acc.wrapping_add(av.wrapping_mul(bv));
        i += 1;
    }
    acc
}
