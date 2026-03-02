### 03/01

### 
Update codebase to take codebase inputs from a config file (such as, stock ticker inputs, email for delivery etc.). After the change, run end to end tests to verify everything working.

###
Design change: For agents, if API keys not available, then have agents run web-searches (for news, earnings call, etc.) and collate findings to be used for downstream modules.

###
Update the report generation file to present results in tabular format (one row per stock ticker), followed by detailed reports for each ticker.

###
Update the report generation file to present results in tabular format, one row per stock ticker

### 
Update the agent hook to make the git commit only after tests are passed

###
Finish tasks 2 and tasks 3 -- also, update the kiro setting to create an agentic hook to submit code to git after completion of each task


### 
Can you create a virtual env first and enable the virtual env? Update tasks.md as well

#### (#1) Design document
* Update the design doc to use AWSStrands as the agentic framework, and Claude as the LLM models

#### (#2) Requirements
* Should the system support international exchanges beyond NYSE/NASDAQ? --> No
* Do you have specific data sources in mind for news, earnings, or macro data (e.g., specific APIs)? --> No. Do a web search and stat with the most popular one. Add them to a config file (with timestamp) that we can edit later to add / remove data sources
* Should there be any rate limiting or caching considerations? --> Not required
* Is terminal/CLI the primary interface, or do you need API/web output as well? --> the agent should be able to output the results as a web-report sent to an email address
* The agentic system should be able to log the input, recommendations made, rational for the recommendations, and fedeback received in a database. For later dates, it should be able to cross-reference this database to provide supporting datapoints (from historical recommendation) when making a new recommendation
* For the implementation plan, assign priorities that starts with a simple MVP and incrementally makes it more sophisticated.

#### (#1) Requirements
I want to build a trading-copilot that. The trading-copilot with take a stock-ticker as input. Using one or more agents, It would then research market news, latest company earnings call, macro trends (such as geo-political tension). Finmally, it would aggregate all the output, summariz and analyze them and provide an high-level (bullish or bearish) sentiment for the ticker for the upcoming 1-2 weeks. 