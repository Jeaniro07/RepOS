# Penyidikan (stub Fase 0)

Isolasi di Fase 0 berlapis tetapi **hanya tingkat konfigurasi**: toolset `browser/computer_use/terminal/code_execution/web`
dimatikan, tanpa `mcp_servers`, kebijakan Auto Review `default: deny`, tanpa kontainer komputer.

Batas jujur: model LLM tetap di cloud (isi percakapan keluar ke penyedia model), dan Hermes tunggal tetap punya jaringan.
Isolasi sungguhan (Hermes terpisah di jaringan `internal: true` + model lokal) = Fase 2. Jangan masukkan data perkara
nyata sebelum itu.
