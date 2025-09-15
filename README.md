# Optimal-Routes-in-Manhattan-
This project uses NYC Yello Taxi Trip Data from Kaggle edited for the Manhattan blocks for January 2015. The main goal comprised of two parts:

Part 1 : General analysis.
In this part, I performed preliminary analysis to make better sense of data and to assist with part 2. For example, using the average daily trip counts, I decided to analyze Saturday and Monday since they had the largest difference in trip counts.
  1) Visualize block locations activity based on dropoff/pickup data
  2) Perform Local and Global Moran's I to get a better picture of spatial autocorrelation and hotspot regions 
  3) Compare daily trip counts, including average and for a given week 

Part 2: Optimal route simulation.
In this part, I simulate potential tourist routes from different starting locations and at different start times, with the goal of determining the most efficient route. The three landmarks I chose were Times Square, The Empire State Building, and The Metropolitan Museum of Art. The starting times were 10AM, 12PM, 2PM, and 4PM. I assumed that the tourist would be exploring Times Square for 30 minutes, exploring Empire State for 2 hours, and exploring the MET for 3 hours. The average time it took to travel from one location to another was derived based on the time of the day. 
  1) Build graphs based on different starting landmarks and times using average time as edge weight
  2) Compute the overall node degree of these landmarks to make better sense of traffic activity (dropoff/pickup not limited to Manhattan)
  3) Compare travel times across routes, days, and times, and compare with node degree data

Outcome:
I found that Route 6 (Met -> Empire State -> Times Square) was the fastest route while Route 2 (Times Square -> Met -> Empire State) was the slowest. Distance travelled for each route was the main determiner. There was a correlation between node degree and average travel time for a given hour. The average travel time independent of route peaked earlier for Monday than Saturday. 

Due to the amount of data, I am currently still in the process of analyzing my outcome. I would like to still analyze all routes independently based on time, route, and day to find the best combination. 

Next Steps:
In the future, I would choose routes more wisely so the distance remained the same. I would also want to use actual average congestion data to see how that compares to node degree.

Data: 
Taxi Data: visit https://www.kaggle.com/datasets/elemento/nyc-yellow-taxi-trip-data and go to yellow_tripdata_2015-01.csv                                                                
Block Data: visit https://www.nyc.gov/content/planning/pages/resources/datasets/census-blocks and download "2010 Census Blocks (Clipped to Shoreline"
