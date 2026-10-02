# ReqGuard 自建评测集

36条原创虚构需求，包含完整、缺用户、缺验收、不可衡量、缺边界、数据/接口不清、多目标、范围过大、模糊、缺异常、内部冲突共12类。`requirements.json`保存文本、11项独立问题标签、风险、说明、split与标注状态。

初始标签为AI辅助起草，尚未完成独立人工复核，禁止称为人工金标准。标注指南见`docs/annotation-guide.md`。来源为本项目自行编写，无商业文档复制。每类第3条作为test，24条train/dev与12条test；没有训练模型。样本相似性使泛化结论有限。

在根目录运行`python scripts/evaluate.py`，结果在`results.json`。生成输入脚本`build_dataset.py`保留显式标签来源；人工复核后应直接编辑JSON并更新status，**不要重新运行生成脚本覆盖人工标注**。保留数据SHA256对照版本。
