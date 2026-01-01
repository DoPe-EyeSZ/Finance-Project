# Part Time Finance Tracker

This project helps people, especially those who work part-time, budget their income. 
My experience working 2 part-time jobs showed me income isn't always constant, so I found traditional budgeting difficult.
As a result of this struggle, I decided to make a finance system that allows one's budget to adapt with their change in income.

## Features

- Basic user authentication
- Data visualization with graphs (line graphs and pie charts)
- Soft delete logic to preserve historical data
- Entry, Spending, Deposit, and Unpaid Credit Card logs

## How to Use

1. Create an account
2. Create your expenses and allocate how much of your income you'd want towards them (you can also deposit money directly to an expense or transfer available funds between expenses)
3. Create a new entry (log all income, spending (credit card as well), and deposits)
4. View overall financial and individual expense details (total balance, total spending, total income, total credit balance, total saved)
5. View graphs

## Screenshots/Demo

![Screenshot description](path/to/screenshot.png)

Or link to a demo video if you have one

## Takeaways/Learnings

- I learned how to design and create data models
- Gained experience utilizing and creating relational data tables
- Learned about how to efficiently query through data and overcome common issues like the N+1 problem
- Learned how to build a full-stack web application from scratch using YouTube tutorials that taught basics
- Learned to consider tradeoffs during design stages such as "lazy-loading" vs. "eager-loading"
- Learned how to use Flask
- Learned to use Lucidchart for planning
- **I learned that starting something without a perfect plan is the best plan**

## Memorable Challenges

1. I designed most of my queries inefficiently and ran into N+1 issues because I truly didn't know what was optimal. I overcame this by taking the time to look back at my old work and making all necessary queries before iterating through the queries (average improvement on performance was 90%).

2. I initially designed spending to be separate from other common transactions such as deposits and credit spending. This caused the system to become overly complicated to navigate, so I decided to generalize these behaviors under a transaction data model. Each transaction was distinguished with boolean flags.

3. I unknowingly designed deposits to be untraceable. This resulted in users being unable to make changes. I fixed this by refactoring the entire transaction aspect of this project. As a result, this led to several other internal issues, forcing me to refactor all work. However, I was able to look back and improve my work.

## Reasonings

- I used an ORM rather than pure SQL because this project was my first time dealing with data handling. Though I didn't receive firsthand pure SQL experience, I'm confident that I learned a significant amount about data handling, querying, data modeling, and relational data models.

- I debated using Django over Flask. However, I found that Django was difficult with my little experience. I found Flask more beginner-friendly. Thinking back at my experience trying to learn Django, I have a better understanding and look forward to learning it.

- I decided to use lazy loading rather than eager loading due to user demand. Users would need their entire financial data only when needed and not constantly. For this reason, lazy loading would be a better choice since I wouldn't have to sacrifice response time during basic operations like creating a new entry.

- When visualizing financial data, users must either view them through their entire financial dashboard page or be redirected to their financial dashboard if they want to view it through a link. This is because the system is designed with lazy loading, meaning all their financial data is updated in their dashboard. So, when users view their dashboard, their financial data is fully updated and the graphs reflect recent data.

- I allowed users to input negative income values as a deliberate design choice. Initially, the entry model stored income as a single value, which created a limitation: tracking multiple income sources per entry would require significant refactoring across income entry, savings calculations, and chart data retrieval. Rather than over-engineer the solution at this stage, I opted for flexibility—negative values let users manually correct income mistakes or adjustments without rebuilding core functionality. This tradeoff prioritizes user control and project scope while keeping the door open for future income-tracking enhancements.

## Final Comments

Overall, I think this project was a great experience for me. I received hands-on experience and learned about great tools which I will carry with me during my future career.

## Contact

Email: ryeung0305@gmail.com
