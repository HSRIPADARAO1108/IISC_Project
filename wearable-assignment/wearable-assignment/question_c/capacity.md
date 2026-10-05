# Capacity calculation (Question C, Level 3)

Assumptions: 1 reading per user per second; row payload 20 B (user_id 4 + ts 8 + hr 4 + acc 4);
about 80 B per row on disk once tuple header, alignment and the (user_id, ts) index are added (assumption).

## 1,000 users
1. Rows per day      = 1,000 users x 86,400 s = 86,400,000
2. Writes per second = 1,000 users x 1 reading/s = 1,000 rows/s
3. Rows per month    = 86,400,000 x 30 = 2,592,000,000
4. Raw payload/month = 2,592,000,000 x 20 B = 51.8 GB
5. On-disk/month     = 2,592,000,000 x 80 B = 207 GB  (~0.2 TB)

## 100,000 users
1. Rows per day      = 100,000 users x 86,400 s = 8,640,000,000
2. Writes per second = 100,000 users x 1 reading/s = 100,000 rows/s
3. Rows per month    = 8,640,000,000 x 30 = 259,200,000,000
4. Raw payload/month = 259,200,000,000 x 20 B = 5,184.0 GB
5. On-disk/month     = 259,200,000,000 x 80 B = 20,736 GB  (~20.7 TB)

