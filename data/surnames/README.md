# 示例姓氏数据

这里只保留四个姓氏的课程项目样本：

- 李
- 王
- 张
- 丁

每个目录下是原始的六类文本：基本信息、历代名人、迁徙传播、人口分布、姓氏起源、姓氏文化。

课程项目的完整数据包含 300+ 姓氏，体积较大且包含课程原始素材，没有提交到仓库。需要完整数据时，把同样结构的目录放到 `data/surnames/` 下，再运行：

```bash
python scripts/import_surnames.py
python scripts/seed_demo.py
```

`scripts/seed_demo.py` 会为 `data/surnames/` 下所有姓氏生成省份分布、朝代和少量名人演示数据；当前示例只包括上述四个姓氏。
