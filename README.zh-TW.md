# skill-bench（繁體中文）

**一個技能，真的讓 Claude 把那件事做得更好嗎？** 大多數技能從來沒被量過。skill-bench 用同一種方法、由不同的人重複量：Claude Code 把技能附的小測試案例做兩次，一次沒有技能、一次有技能，再由程式評分它寫出的檔案。至少三位作者以外的人結果一致，才算數。

看[蟻窩儀表板](https://opencolony-ai.github.io/skill-bench/colony.html?lang=zh)（每個技能、誰驗證過、點數）和[報告](https://opencolony-ai.github.io/skill-bench/zh-TW.html)：每個技能一張卡，下面是沒裝和裝了技能時 Claude 寫的東西並排。

## 怎麼看結果

- **結果**：題目本身要求的事，沒裝技能的 Claude 也有公平的機會做到；不看格式（寫「L3」「line 3」「第 3 行」都算）。
- **照技能做**：技能自己規定的規則，每一條都引用技能原句，測試會檢查原句真的在技能裡；技能沒寫的規則不准考。
- **token 用量、時間**：整組案例實際用掉的 token 和秒數。大家用自己訂閱方案的額度跑，不另外花錢，所以只看 token，不看美元。
- 一句話結論照固定規則產生：先看結果有沒有變好或變差，再看是不是只改了格式，最後看 token 多用或少用多少。照技能做不算「做得更好」，因為沒裝技能的 Claude 根本不知道那些規則。

## 幫忙驗證一個技能（約 5 分鐘）

需要 Python 3.10 以上、已登入的 Claude Code，以及這個 repo 的 fork。

```bash
python bench.py next --user <你的 GitHub 帳號>
```

```bash
python bench.py run <技能名稱>
```

```bash
python bench.py submit <它印出的資料夾> --user <你的 GitHub 帳號>
```

然後把 `results/` 底下新增的那一個檔案開成 pull request。

- 技能由程式替你挑，不能自己選，也不會挑到自己寫的或已經驗證過的技能。
- 執行在系統暫存資料夾進行，Claude 只能讀寫檔案，不能執行指令、不能上網。
- 一次驗證是兩次 Claude Code 執行。實測 `conventional-commit`（3 個案例、Sonnet）：約 1–2 分鐘、幾十萬 token（大多是 Claude Code 自己的提示詞，從快取讀取），用的是你訂閱方案的額度，不另外花錢。
- **模型不經驗證**，靠多人一致把關。

- 執行時不載入你自己的技能、外掛和 MCP 伺服器，兩次都只看得到 Claude Code 內建的技能，加上這次要量的那一個。
- 每筆結果會記錄 Claude 呼叫了哪些工具、有沒有打開這個技能。Claude 根本沒打開的技能幫不上忙，排行榜會列出發生幾次。

規則與新增技能的方法見 [README.md](README.md)。
