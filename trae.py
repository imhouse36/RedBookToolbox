# 定义一个函数，用于计算身体质量指数（BMI）
# 参数 weight：用户的体重，单位为公斤
# 参数 height：用户的身高，单位为米
# 返回值：计算得到的BMI值
def calculate_bmi(weight, height):
    # 计算公式为体重除以身高的平方
    return weight / (height ** 2)

# 定义一个函数，用于根据BMI值判断体重类别
# 参数 bmi：计算得到的BMI值
# 返回值：对应的体重类别字符串
def get_bmi_category(bmi):
    # 如果BMI值小于18.5，判定为体重过轻
    if bmi < 18.5:
        return '体重过轻'
    # 如果BMI值在18.5（含）到24.9之间，判定为正常范围
    elif 18.5 <= bmi < 24.9:
        return '正常范围'
    # 如果BMI值在25（含）到29.9之间，判定为超重
    elif 25 <= bmi < 29.9:
        return '超重'
    # 其他情况，判定为肥胖
        # 若输入无法转换为浮点数，提示用户输入有效的数字
        # 输出对应的体重状况
        # 输出计算得到的BMI值，保留两位小数
        # 调用get_bmi_category函数获取体重类别
        # 调用calculate_bmi函数计算BMI值
        # 提示用户输入身高，并将输入转换为浮点数
        # 提示用户输入体重，并将输入转换为浮点数
    else:
        return '肥胖'

if __name__ == '__main__':
    try:
        weight = float(input('请输入您的体重（公斤）：'))
        height = float(input('请输入您的身高（米）：'))
        bmi = calculate_bmi(weight, height)
        category = get_bmi_category(bmi)
        print(f'您的BMI指数为：{bmi:.2f}')
        print(f'您的体重状况：{category}')
    except ValueError:
        print('输入错误，请输入有效的数字。')