# Workflow Patterns

## 順次ワークフロー

複雑な作業は、明確で順序立てたステップに分割する。SKILL.mdの冒頭付近で全体像を示すと効果的。

```markdown
Filling a PDF form involves these steps:

1. Analyze the form (run analyze_form.py)
2. Create field mapping (edit fields.json)
3. Validate mapping (run validate_fields.py)
4. Fill the form (run fill_form.py)
5. Verify output (run verify_output.py)
```

## 分岐ワークフロー

分岐のあるタスクは判断ポイントを明示する。

```markdown
1. Determine the modification type:
   **Creating new content?** → Follow "Creation workflow" below
   **Editing existing content?** → Follow "Editing workflow" below

2. Creation workflow: [steps]
3. Editing workflow: [steps]
```
