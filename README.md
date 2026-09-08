# FIT5196 A1 — Group030

本仓库用于完成 Group030 的 FIT5196 Assessment 1。项目从分配的 JSON 和 XML 原始数据开始，完成数据检查、清理、跨来源合并、六张关系表生成、验证和 EDA。

## 文件目录说明

请尽量按照下面的目录分工保存文件，避免把过程文件和最终提交文件混在一起。

```text
FIT5196-A1/
├── assignment_materials/       # 教学团队提供的文件
│   ├── allocated_package/      # 原始 ZIP、JSON、XML、数据字典和 manifest
│   ├── specification/          # 作业要求和评分标准
│   └── templates/              # Solution、EDA、Mapping 和 AI 声明模板
├── processing/                 # 我们的数据处理与分析过程
│   ├── notebooks/              # Group030_solution.ipynb 和 Group030_EDA.ipynb
│   ├── code/                   # Notebook 导出的 Python 文件、文本函数和构建脚本
│   ├── mapping/                # Source-to-target mapping
│   ├── outputs/                # 六张标准化 CSV 和 validation register
│   ├── figures/                # EDA 生成的 Figure 1–8
│   ├── report/                 # PDF 生成过程中使用的 HTML 报告
│   └── assets/                 # 报告使用的校徽等静态资源
├── AI_records/                 # AI 对话记录、AI index 和待签署声明工作文件
├── Group030_EDA.pdf            # 最终提交的 EDA 报告
├── Group030_A1_submission.zip  # 最终 Moodle 提交压缩包（最后检查后生成）
├── SUBMISSION_CHECKLIST.md     # 提交前检查清单
├── requirements.txt            # Python 依赖
└── README.md                   # 项目和目录说明
```

根目录主要保留老师最终需要查看或提交的文件。Notebook、代码、CSV、图片和报告生成文件统一放在 `processing/` 下；老师提供的原始材料不要修改，统一保留在 `assignment_materials/`。

## 重新运行项目

在项目根目录依次运行：

```bash
python3 processing/code/Group030_solution.py
python3 processing/code/Group030_EDA.py
```

第一条命令从原始 JSON 和 XML 重新生成六张标准化 CSV 及 validation register。第二条命令从六张 CSV 重新生成 Figure 1–8 和 EDA PDF。两个流程均可离线运行。

两份主要 Notebook 位于 `processing/notebooks/`，均为可以独立运行的完整版本，不会反向导入对应 Python 文件中的主流程。

修改 Notebook 后，使用下面的命令重新导出对应 Python 文件：

```bash
python3 processing/code/build/export_notebook_scripts.py
```

完成 AI 记录并收集所有成员签名后，使用下面的命令生成 Moodle 压缩包：

```bash
python3 processing/code/build/build_final_submission.py
```

## 提交注意事项

最终上传 Moodle 的文件是项目根目录下的 `Group030_A1_submission.zip` 和 `Group030_EDA.pdf`。原始 JSON、XML 和老师提供的材料不会被放入最终提交压缩包。

最终打包前，请确认：

- 所有组员已经检查自己的姓名和学号；
- 所有组员已经签署 `Group030_AI_declaration.pdf`；
- 真实、完整的 AI 对话记录和英文 AI index 已放在 `AI_records/`；
- 两份 Notebook 已完成 Restart & Run All；
- 六张 CSV、八张图和最终 PDF 均由当前版本代码重新生成。
