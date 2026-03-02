## 03/02

##
The evaluation report only being generated for APPL -- update the runner script to generate it for all tickers (in config) and generate a consolidated report similar to "trading_copilot_report"

##
Update the format of "evaluation_report" to the same as "trading_copilot_report", i.e., a single report with multiple ticker information, with a summarized table on the top, links of detailed results below, and a "back to top" link at the end of each detailed results section.


## 03/01

###
In the HTML report, for each ticker, 
1. provide a rationale (or justification) on the sentiment provided.
2. in the rationale (or justification), explicity highlight or cite information from the news information retrieved

###
In additon to google news, pull news from other channels (CNBC, Wall Street Journal, Bloomberg).
Combine results and present a final sentiment.
Present all news article in "Detailed Analysis" for each ticker.

###
In the HTML report, show all recent headlines, hyperlink the headline, reduce font, and make the output more compact

###
The HTML report says missing earnings. Fix this.

###
In the HTML report, all "Readmore" links point to "example.com"
I also don't see information from any actual web-searched financial domains or news outlet.
Finally, also add an agent to collate information from "reddit channels" for the respective tickers.
Generate a new HTML report based on the above.

### 
In the HTML report,
1. in the top table, for each ticker, add a link to detailed report for each ticker
2. at the bottom of detailed report for each ticker, add a link to get back to the top executive table
3. reduce font size, increase text density, and make the report compact and with more professional looks

###
Update the codebase to achieve the following:
1. in the detailed report for each ticker, for each findings (recent headlines, earning call, etc.) provide the reference weblink from this information was collected
2. the reference weblink must exist online

###
If API keys are not present (for news, earning calls, etc.), the system should do web-search to collect content and use that information for downstream components.
Implement this. Run end-to-end and generate a real report (and not using mock data).

###
The html report was supposed to have a summarized table at top (one row per ticker) followed by the detailed results (i.e., current content). Update code to fix this.

### Initial
This codebase researches financial information (news, earning calls) for stock tickers and send a sentiment analysis report. 
The stock tickers and email delivery is provided in appConfig.yaml
Run the code end to end to ensure it is working -- propose fixes if something broken.