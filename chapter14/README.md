# Chapter 14

## Main question
How to get from point A to B in NYC as fast as possible?

## Mini project structure
1. A rest API for serving City Bike data
2. One file share serving Yellow Cab taxi data
3. MinIO, an object store that supports the S3 protoclo (
   see chapter 07)
4. PostgreSQL database for querying and storing data
5. A Flask application displaying the results

## Data endpoints
The data is available on the following endpoints:
1. Yellow Cab data: http://localhost:8081
2. Citi Bike data: http://localhost:8082

## My implementation steps
1. taxi_db - pull the data from s3 online storage and store it to
postgresql database (see notes below).


### Taxi_db notes
I like using with newish things. So I looked up the availability
of the data for 2021. But at the time of writing, the data for
2021 is available up to July. To keep things simple, I'm gonna
use the data from 2020.
Just like the author states in the GitHub repo for the book,
the docker image will become very large if we take all of the
data. Therefore, data is taken only every X lines.
