# Quickstart: Re-apply simulation settings

1. Offline: `.venv\Scripts\python.exe -m unittest discover -s tests/unit -t .` → PASS.
2. Board1 copy (user OK first): `tests/isim_check.py <ws> --reapply <request with applied CPHY_U14_U26>`:
   - re-apply with `cleanup.gnd_via_keep_dist_mm` changed → refused naming the key;
   - re-apply sweep stop 20 GHz + max passes 20 → backup `final/CPHY_U14_U26_old_<time>.aedb` exists; self-check OK
     (reads 20 GHz / 20 passes); geometry metrics equal to the previous apply; `user_settings.json` history has the old
     values; a merged interface goes back to `applied`.
