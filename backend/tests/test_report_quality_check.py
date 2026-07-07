import unittest

from app.services.report_quality_check import check_report_quality


def make_report(extra_body: str = "", include_plan_c: bool = True) -> str:
    plan_c = "### Plan C：系统建议路径\n1. 内容\n" if include_plan_c else ""
    return f"""
# 我的生涯蓝图
## 一、你5—10年后的人生画像
{extra_body or "内容"}
## 二、你的核心优势与风险短板
内容
## 三、人生愿景与当前路径的匹配度诊断
### 你现在最大的困惑是什么？
不知道未来适合做什么
### 这个困惑背后的真正问题是什么？
需要验证目标岗位和自身能力之间的匹配。
### 接下来可以如何验证？
通过访谈、项目和实习验证。
### Plan A：主攻路径
1. 内容
### Plan B：备选路径
1. 内容
{plan_c}
## 四、接下来6个月，你可以做的3—5件事
内容
## 五、半年后我会问你这些问题
内容
## 六、一个值得你长期思考的问题
内容
## 安全提醒
本报告不是医学诊断、心理诊断或人生终局结论。如持续感到焦虑、低落或无力，应联系学校心理咨询中心；升学就业的具体政策与机会应向学校就业指导中心、教务部门或官方渠道核实。
""".strip()


class ReportQualityCheckTest(unittest.TestCase):
    def test_length_warnings_do_not_fail_report(self):
        content = make_report(extra_body="内容" * 3000)

        quality = check_report_quality(content, expected_confusions=["不知道未来适合做什么"])

        self.assertEqual(quality["status"], "warning")
        self.assertEqual(quality["fatalWarnings"], [])
        self.assertTrue(any("报告长度超过" in item or "模块超过" in item for item in quality["warnings"]))

    def test_missing_required_plan_is_fatal(self):
        content = make_report(include_plan_c=False)

        quality = check_report_quality(content, expected_confusions=["不知道未来适合做什么"])

        self.assertEqual(quality["status"], "failed")
        self.assertTrue(any("Plan C" in item for item in quality["fatalWarnings"]))

    def test_missing_exact_confusion_reference_is_warning(self):
        content = make_report()

        quality = check_report_quality(content, expected_confusions=["纠结就业、读研、出国、读博"])

        self.assertEqual(quality["status"], "warning")
        self.assertEqual(quality["fatalWarnings"], [])
        self.assertIn("缺少当前困惑选项引用", quality["warnings"])


if __name__ == "__main__":
    unittest.main()
