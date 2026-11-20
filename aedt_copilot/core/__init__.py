"""Lớp core của aedt_copilot: dùng chung cho mọi feature, KHÔNG import package feature nào
(cut_board, pi_dc, edit_layout, interface_sim, cli, mcp_server).

    errors        CopilotInputError, RegistryError
    validate      require_type / require_number / require_int / require_choice / require_text / require_path
    config        machine() (config.yaml), template_rows(csv), coerce(), template_path()
    edb           aedb_path(), open_edb(), edb_session()  (bọc aedt_env.open_edb)
    geometry      hình học 2D thuần (m)        geometry_edb   prim_points(primitive EDB)
    units         m <-> mm, m2 <-> mm2, edb_length()
    registry      load(package) -> các entry (NAME, ORDER, run) theo thứ tự

Contract: specs/002-architecture-core/contracts/core-*.md
"""
