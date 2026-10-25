---
skill_name: apache-spark-patterns
description: Master Apache Spark with RDDs, DataFrames, partitioning, caching, joins, and performance tuning
category: Database & Data
version: 1.0.0
---

# Apache Spark Patterns

Apache Spark enables distributed data processing at scale.

## RDDs vs DataFrames

```python
# RDD: Lower-level, less optimized
rdd = sc.textFile("s3://bucket/data.txt")
rdd_filtered = rdd.filter(lambda x: len(x) > 0)
rdd_mapped = rdd_filtered.map(lambda x: (x.split()[0], 1))
counts = rdd_mapped.reduceByKey(lambda a, b: a + b)
counts.collect()

# DataFrame: Higher-level, optimized by Catalyst
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("analytics").getOrCreate()

df = spark.read.csv("s3://bucket/data.csv", header=True)
df_filtered = df.filter(df.age > 18)
df_agg = df_filtered.groupBy("region").agg(
    count("*").alias("count"),
    avg("salary").alias("avg_salary")
)
df_agg.show()

# DataFrames are preferred for most use cases
# - Automatically optimized by Catalyst
# - Better performance
- Support SQL
```

## Partitioning Strategy

```python
# Repartition for balance
df_balanced = df.repartition(200)

# Repartition by column (for shuffle operations)
df_partitioned = df.repartition("customer_id")

# Coalesce to reduce partitions (no full shuffle)
df_coalesced = df.coalesce(50)

# Custom partition count
spark.conf.set("spark.sql.shuffle.partitions", "200")

# Check partition count
print(f"Partitions: {df.rdd.getNumPartitions()}")

# Check partition sizes
def get_partition_sizes(df):
    return df.rdd.mapPartitions(
        lambda it: [sum(1 for _ in it)]
    ).collect()

print(get_partition_sizes(df))
```

## Caching and Persistence

```python
from pyspark import StorageLevel

# Cache in memory
df.cache()  # Equivalent to MEMORY_AND_DISK

# Different storage levels
df.persist(StorageLevel.MEMORY_ONLY)        # Fastest, may spill
df.persist(StorageLevel.MEMORY_AND_DISK)    # Recommended
df.persist(StorageLevel.DISK_ONLY)          # Slowest
df.persist(StorageLevel.OFF_HEAP)           # For large datasets

# Use cache when:
# - DataFrame is used multiple times
# - Expensive transformation (many shuffles)
# - Iterative algorithms

# Remove cache
df.unpersist()

# Example: Cache intermediate result
df_filtered = spark.read.parquet("data.parquet").filter(col("status") == "active")
df_filtered.cache()

# Use it multiple times
count1 = df_filtered.count()
stats = df_filtered.describe().collect()
```

## Join Operations

```python
from pyspark.sql.functions import broadcast

# Broadcast join (small table)
large_df = spark.read.parquet("large_table.parquet")
small_df = spark.read.parquet("small_table.parquet")

# Broadcast small_df to all executors
result = large_df.join(
    broadcast(small_df),
    large_df.id == small_df.id,
    "inner"
)

# Sort merge join (large + large)
df1_sorted = df1.sortBy("key").repartition(200)
df2_sorted = df2.sortBy("key").repartition(200)

result = df1_sorted.join(df2_sorted, "key")

# Left anti join (rows in left not in right)
result = df1.join(df2, "key", "left_anti")

# Left semi join (rows in left that match right)
result = df1.join(df2, "key", "left_semi")

# Join on multiple columns
result = df1.join(
    df2,
    (df1.key1 == df2.key1) & (df1.key2 == df2.key2),
    "inner"
)
```

## Window Functions

```python
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number, rank, lag, lead

# Define window
window = Window.partitionBy("customer_id").orderBy("date")

# Row number
df_ranked = df.withColumn(
    "rn",
    row_number().over(window)
)

# Rank with gaps
df_ranked = df.withColumn(
    "rank",
    rank().over(window)
)

# Lead/lag (access adjacent rows)
df_with_lag = df.withColumn(
    "previous_amount",
    lag("amount").over(window)
)

# Running sum
window_sum = Window.partitionBy("customer_id") \
    .orderBy("date") \
    .rangeBetween(Window.unboundedPreceding, Window.currentRow)

df_running = df.withColumn(
    "cumulative_sum",
    sum("amount").over(window_sum)
)

# Top-N per group
window_top = Window.partitionBy("category") \
    .orderBy(desc("sales")) \
    .rowsBetween(Window.unboundedPreceding, Window.currentRow)

df_top = df.withColumn("rank", row_number().over(window_top)) \
    .filter(col("rank") <= 5)
```

## Performance Tuning

```python
# Shuffle partitions (default 200)
spark.conf.set("spark.sql.shuffle.partitions", "400")

# Broadcast threshold (auto-broadcast tables < 10MB)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "50MB")

# Enable adaptive query execution
spark.conf.set("spark.sql.adaptive.enabled", True)
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", True)

# Enable dynamic partition pruning
spark.conf.set("spark.sql.dynamicPartitionPruning.enabled", True)

# Executor configuration
spark.conf.set("spark.executor.memory", "8g")
spark.conf.set("spark.executor.cores", "4")
spark.conf.set("spark.driver.memory", "4g")

# Example: Optimize large join
orders_df = spark.read.parquet("orders.parquet")
customers_df = spark.read.parquet("customers.parquet")

# Coalesce large table before join
orders_coalesced = orders_df.coalesce(50)
customers_cached = customers_df.cache()

result = orders_coalesced.join(customers_cached, "customer_id")
```

## Real-World Patterns

```python
# Data quality checks
from pyspark.sql.functions import col, count, when

def data_quality_report(df, table_name):
    """Generate data quality metrics"""
    total_rows = df.count()

    quality_metrics = df.select([
        count(when(col(c).isNull(), 1)).alias(f"{c}_nulls")
        for c in df.columns
    ]).collect()[0]

    print(f"Table: {table_name}")
    print(f"Total rows: {total_rows}")
    for col_name, null_count in quality_metrics.asDict().items():
        print(f"{col_name}: {null_count} nulls ({null_count/total_rows*100:.2f}%)")

data_quality_report(df, "customers")

# Incremental load pattern
def incremental_load(spark, source_path, dest_table, key_col):
    """Load new/modified records"""
    new_df = spark.read.parquet(source_path)

    if spark.catalog.tableExists(dest_table):
        existing_df = spark.read.table(dest_table)
        max_date = existing_df.agg({"updated_at": "max"}).collect()[0][0]

        new_df = new_df.filter(col("updated_at") > max_date)

    new_df.write.insertInto(dest_table)

# String aggregation
from pyspark.sql.functions import collect_list, concat_ws

df_agg = df.groupBy("category").agg(
    concat_ws(", ", collect_list("product_name")).alias("products")
)
```

Apache Spark powers large-scale data processing pipelines.
