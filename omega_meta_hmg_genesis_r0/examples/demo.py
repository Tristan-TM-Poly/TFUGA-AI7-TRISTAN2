from omega_meta_hmg import GeneratorGenome, MetaHMGEngine, Residual, FrozenBenchmark

engine = MetaHMGEngine()
residuals = [Residual("semantic-loss", 6.0, 0.15), Residual("compute-debt", 3.0, 0.1)]
genome = GeneratorGenome("demo-generator", "reduce verified residual", ("EXP", "PROJECT", "VERIFY", "COMPRESS"), budget=7)
benchmark = FrozenBenchmark("demo-frozen-r0", 3.0, 0.2, 0.3, 6.0)
pressure = engine.residualize(residuals)
candidates = engine.generate_candidates(genome, residuals)
winner, results = engine.tournament(candidates, benchmark, pressure)
print("residual_pressure=", round(pressure, 3))
for c, r in zip(candidates, results): print(c.representation, r.status.value, round(r.score, 3), round(c.utility, 3))
if winner:
    result = next(r for r in results if r.candidate_id == winner.candidate_id)
    cert = engine.certify(residuals, winner, result)
    crystal = engine.distill(winner, cert)
    print("winner=", winner.representation)
    print("receipt=", cert.receipt_hash)
    print("regeneration_exact=", engine.regenerate(crystal, winner) == winner)
