from __future__ import annotations


_X86_INDEXED = r'''.text
.globl omega_dot_u64_indexed
.type omega_dot_u64_indexed,@function
omega_dot_u64_indexed:
    xorq %rax, %rax
    xorq %rcx, %rcx
.Lomega_dot_u64_indexed_loop:
    cmpq %rdx, %rcx
    jae .Lomega_dot_u64_indexed_done
    movq (%rdi,%rcx,8), %r8
    imulq (%rsi,%rcx,8), %r8
    addq %r8, %rax
    incq %rcx
    jmp .Lomega_dot_u64_indexed_loop
.Lomega_dot_u64_indexed_done:
    ret
.size omega_dot_u64_indexed, .-omega_dot_u64_indexed
'''

_X86_POINTER = r'''.text
.globl omega_dot_u64_ptr
.type omega_dot_u64_ptr,@function
omega_dot_u64_ptr:
    xorq %rax, %rax
    testq %rdx, %rdx
    je .Lomega_dot_u64_ptr_done
.Lomega_dot_u64_ptr_loop:
    movq (%rdi), %r8
    imulq (%rsi), %r8
    addq %r8, %rax
    addq $8, %rdi
    addq $8, %rsi
    decq %rdx
    jne .Lomega_dot_u64_ptr_loop
.Lomega_dot_u64_ptr_done:
    ret
.size omega_dot_u64_ptr, .-omega_dot_u64_ptr
'''

_AARCH64_POINTER = r'''.text
.globl omega_dot_u64_ptr
.type omega_dot_u64_ptr,%function
omega_dot_u64_ptr:
    mov x3, #0
    cbz x2, .Lomega_dot_u64_ptr_done
.Lomega_dot_u64_ptr_loop:
    ldr x4, [x0], #8
    ldr x5, [x1], #8
    mul x4, x4, x5
    add x3, x3, x4
    subs x2, x2, #1
    b.ne .Lomega_dot_u64_ptr_loop
.Lomega_dot_u64_ptr_done:
    mov x0, x3
    ret
.size omega_dot_u64_ptr, .-omega_dot_u64_ptr
'''


def supported_variants(architecture: str) -> tuple[str, ...]:
    architecture = architecture.lower().replace("-", "_")
    if architecture in {"x86_64", "amd64"}:
        return ("indexed", "ptr")
    if architecture in {"aarch64", "arm64"}:
        return ("ptr",)
    raise ValueError(f"unsupported architecture: {architecture}")


def emit_dot_u64(architecture: str = "x86_64", variant: str = "ptr") -> str:
    architecture = architecture.lower().replace("-", "_")
    variant = variant.lower()
    if architecture in {"x86_64", "amd64"}:
        if variant == "indexed":
            return _X86_INDEXED
        if variant == "ptr":
            return _X86_POINTER
    elif architecture in {"aarch64", "arm64"} and variant == "ptr":
        return _AARCH64_POINTER
    raise ValueError(
        f"unsupported architecture/variant pair: {architecture}/{variant}; "
        f"supported={supported_variants(architecture)}"
    )


def static_instruction_count(assembly: str) -> int:
    count = 0
    for raw_line in assembly.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(".") or line.endswith(":") or line.startswith("#"):
            continue
        count += 1
    return count
