import csv
import time
import random
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def crawl_pages(num_pages=3):
    data = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # 可改为False更拟人
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": random.randint(1200, 1400), "height": random.randint(700, 900)},
            locale="zh-CN"
        )
        page = context.new_page()
        page.goto("https://www.lottery.gov.cn/kj/kjlb.html?dlt")
        page.wait_for_selector("iframe#iFrame1")
        frame = page.frame(name="iFrame1")
        for _ in range(num_pages):
            # 随机等待，模拟人操作
            time.sleep(random.uniform(1.5, 3.5))
            # 随机滚动
            scroll_y = random.randint(100, 500)
            frame.evaluate(f"window.scrollTo(0, {scroll_y})")
            soup = BeautifulSoup(frame.content(), "html.parser")
            table = soup.find("table", class_="m-historyTab")
            if table is None:
                print("没找到表格，结构可能变了。")
                break
            rows = table.find("tbody").find_all("tr")
            # 记录当前页第一个期号
            first_qh = rows[0].find_all("td")[0].get_text(strip=True) if rows and len(rows[0].find_all("td")) > 0 else ""
            for row in rows:
                tds = row.find_all("td")
                if len(tds) < 9:
                    continue
                qh = tds[0].get_text(strip=True)
                date = tds[1].get_text(strip=True)
                qianqu = [td.get_text(strip=True) for td in tds[2:7]]
                houqu = [td.get_text(strip=True) for td in tds[7:9]]
                if len(qianqu) == 5 and len(houqu) == 2:
                    data.append([qh, date] + qianqu + houqu)

            # 获取当前页码
            pager = soup.find("ul", class_="m-pager")
            current_page = 1
            if pager:
                active = pager.find("li", class_="number active")
                if active:
                    try:
                        current_page = int(active.get_text(strip=True))
                    except:
                        pass

            # 翻到下一页
            next_page = current_page + 1
            frame.evaluate(f"kjCommonFun.goNextPage({next_page})")

            # 等待新内容加载（期号变化）
            for _ in range(20):
                time.sleep(0.5)
                soup_new = BeautifulSoup(frame.content(), "html.parser")
                table_new = soup_new.find("table", class_="m-historyTab")
                if table_new:
                    rows_new = table_new.find("tbody").find_all("tr")
                    new_first_qh = rows_new[0].find_all("td")[0].get_text(strip=True) if rows_new and len(rows_new[0].find_all("td")) > 0 else ""
                    if new_first_qh != first_qh:
                        break
        browser.close()
    return data

if __name__ == "__main__":
    num_pages = int(input("请输入要爬取的页数: "))
    data = crawl_pages(num_pages)
    with open("dlt.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["期号", "开奖日期", "前区1", "前区2", "前区3", "前区4", "前区5", "后区1", "后区2"])
        writer.writerows(data)
    print(f"已保存 {len(data)} 条数据到 dlt.csv")

    # 统计前区和后区号码出现频率
    from collections import Counter
    qianqu_nums = []
    houqu_nums = []
    for row in data:
        qianqu_nums.extend(row[2:7])
        houqu_nums.extend(row[7:9])
    qianqu_counter = Counter(qianqu_nums)
    houqu_counter = Counter(houqu_nums)
    top5_qianqu = qianqu_counter.most_common(5)
    top2_houqu = houqu_counter.most_common(2)
    print("前区出现频率最高的5个号码:")
    for num, count in top5_qianqu:
        print(f"号码: {num}, 出现次数: {count}")
    print("后区出现频率最高的2个号码:")
    for num, count in top2_houqu:
        print(f"号码: {num}, 出现次数: {count}")

    # 新增：统计出现频率最低的号码
    low5_qianqu = qianqu_counter.most_common()[-5:]
    low2_houqu = houqu_counter.most_common()[-2:]
    print("前区出现频率最低的5个号码:")
    for num, count in low5_qianqu:
        print(f"号码: {num}, 出现次数: {count}")
    print("后区出现频率最低的2个号码:")
    for num, count in low2_houqu:
        print(f"号码: {num}, 出现次数: {count}")

    # 前区和后区所有可能的号码
    all_qianqu = {f"{i:02d}" for i in range(1, 36)}
    all_houqu = {f"{i:02d}" for i in range(1, 13)}

    # 已出现过的号码集合
    appeared_qianqu = set(qianqu_nums)
    appeared_houqu = set(houqu_nums)

    # 没有出现过的号码
    not_appeared_qianqu = sorted(all_qianqu - appeared_qianqu)
    not_appeared_houqu = sorted(all_houqu - appeared_houqu)

    print("历史数据中完全没有出现过的前区号码：", not_appeared_qianqu)
    print("历史数据中完全没有出现过的后区号码：", not_appeared_houqu)

    # 选热号
    hot_qianqu = [num for num, _ in top5_qianqu]
    hot_houqu = [num for num, _ in top2_houqu]
    # 选冷号
    cold_qianqu = [num for num, _ in low5_qianqu]
    cold_houqu = [num for num, _ in low2_houqu]

    # 混沌选号
    chaos_qianqu = set()
    if len(hot_qianqu) >= 2:
        chaos_qianqu.update(random.sample(hot_qianqu, 2))
    if len(cold_qianqu) >= 2:
        chaos_qianqu.update(random.sample(cold_qianqu, 2))
    if not_appeared_qianqu:
        chaos_qianqu.add(random.choice(not_appeared_qianqu))
    while len(chaos_qianqu) < 5:
        chaos_qianqu.add(f"{random.randint(1,35):02d}")

    chaos_houqu = set()
    if hot_houqu:
        chaos_houqu.add(random.choice(hot_houqu))
    if not_appeared_houqu:
        chaos_houqu.add(random.choice(not_appeared_houqu))
    while len(chaos_houqu) < 2:
        chaos_houqu.add(f"{random.randint(1,12):02d}")

    print("混沌算法推荐：")
    print("前区：", " ".join(sorted(chaos_qianqu)))
    print("后区：", " ".join(sorted(chaos_houqu)))