# conflict-parser

> **Parse, analyse, and resolve Git merge-conflict files in pure Python**

`conflict-parser` turns any file that contains Git conflict markers
(`<<<<<<<`, `|||||||`, `=======`, `>>>>>>>`) into a structured,
easy-to-inspect object.
No external dependencies, no shelling out to Git — just a small,
single-pass state machine.

---

## ✨ Features

- **Supports both conflict styles**
  _merge_ (`<<<<<<< / ======= / >>>>>>>`) and _diff3_
  (`<<<<<<< / ||||||| / ======= / >>>>>>>`)
- **Line-accurate segmentation** into:
  - `ContextSegment` – unchanged regions
  - `ConflictSegment` – full metadata + separate _ours/base/theirs_ lines
- **Round-trip safe** – regenerate the exact original text
- **One-liner conflict resolution** – `take_ours` / `take_theirs`
- **Pure Python ≥ 3.10**, zero run-time dependencies
- Typed everywhere (PEP 561) & 100 % test coverage via `pytest`

---

## 📦 Installation

```bash
pip install conflict-parser
```

---

## 🚀 Quick-start

```python
from conflict_parser import MergeMetadata, MergedFile

raw = (
    "line1\n"
    "<<<<<<< HEAD\n"
    "ours1\n"
    "ours2\n"
    "=======\n"
    "theirs1\n"
    "theirs2\n"
    ">>>>>>> feature-branch\n"
    "line_after\n"
)

# 1) Parse --------------------------------------------------------------
meta = MergeMetadata(conflict_style="merge")      # or "diff3"
mf   = MergedFile.from_content("demo.txt", raw, meta)

print(len(mf.segments))           # → 3  (context / conflict / context)

# 2) Inspect ------------------------------------------------------------
for seg in mf.segments:
    if isinstance(seg, ConflictSegment):
        print(seg.ours_label, seg.theirs_label, seg.ours_lines)

# 3) Recreate the original text ----------------------------------------
assert mf.to_original_content() == raw

# 4) Resolve by keeping OUR side ---------------------------------------
clean = mf.resolve_conflicts("take_ours")
```

---

## 🧩 API in 60 seconds

| Object            | What it represents                                    |
| ----------------- | ----------------------------------------------------- |
| `MergeMetadata`   | Chosen conflict style (`merge`/`diff3`) & marker size |
| `ContextSegment`  | Uncontested block (`start_line_no`, `lines`)          |
| `ConflictSegment` | One conflict chunk; labels & _ours/base/theirs_ text  |
| `MergedFile`      | Wrapper holding **ordered** segments + helper methods |

### MergedFile helpers

| Method                                    | Purpose                                                |
| ----------------------------------------- | ------------------------------------------------------ |
| `to_original_content()`                   | Losslessly regenerate the original conflicted file     |
| `resolve_conflicts(strategy="take_ours")` | Remove markers and keep either _ours_ or _theirs_ side |

---

## 🔬 Testing

```bash
git clone https://github.com/jinu-jang/conflict-parser
cd conflict-parser
pip install -e ".[dev]"
pytest -q
```

All tests should pass — see `tests/` for comprehensive use-cases.

---

## 🤝 Contributing

Pull requests are welcome!
Please run `black . && isort . && pytest` before submitting.

1. **Fork** → **feature branch** → **PR**
2. Add/adjust tests for any new behaviour
3. Follow conventional commit messages

---

## 📄 License

Released under the MIT License © 2025 Jinu Jang.
