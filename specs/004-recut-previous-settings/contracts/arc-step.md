# Contracts: arc step (`setup.arc_step_deg`)

Tests: `tests/unit/test_arc_step.py`; board1: `tests/regression.py` (reference `arc_step_deg` 10).

- Template row: `setup.arc_step_deg,Arc step size,deg,num,channel,no,10,HFSS circle and arc approximation (Advanced Meshing)`.
- `cut_board.config.build_params`: error `setup.arc_step_deg: phải > 0 và <= 90` when outside (0, 90] (same style
  as the sweep rule messages).
- `cut_board.cutter.apply_setup(edb, P, log)`: sets `st.curve_approx_settings.arc_angle = f"{P['setup']['arc_step_deg']:g}deg"`;
  error → log line, cut continues (same as other setup items); the self-check then reports the mismatch.
- `interface_sim.apply.read_setup`: `setup.arc_step_deg` = float of `arc_angle` without `deg`;
  `expected_setup`: `float(P['setup']['arc_step_deg'])`.
- `cutter.metrics` adds `arc_step_deg` (read back) so `tests/regression.py` can check it for the Excel flow.
