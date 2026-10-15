# task_management

タスク管理

## セットアップ

PowerShell では `py -3`、bash では `python3` を使う。

```powershell
py -3 -m pip install -r requirements.txt
```

```bash
python3 -m pip install -r requirements.txt
```

## テスト

```powershell
py -3 -m unittest discover -s tasks/_scripts -p "test_*.py"
```

```bash
python3 -m unittest discover -s tasks/_scripts -p "test_*.py"
```
