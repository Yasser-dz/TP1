from datetime import datetime, timedelta
import json
import boto3
import pandas as pd
import matplotlib.pyplot as plt
class MetricGenerator:
    """ Metric generator used to retrieve CloudWatch metrics of target groups 
    and generate plots.
    """

    def __init__(self, elb_id, cluster_t2_id, cluster_m4_id, cluster_t2_instances_ids, cluster_m4_instances_ids):
        """Initiate MetricGenerator and print ELB and Cluster IDs."""
        self.cloudwatch = boto3.client('cloudwatch')
        self.elb_id = elb_id
        self.cluster_t2_id = cluster_t2_id
        self.cluster_m4_id = cluster_m4_id        
        self.cluster_t2_instances_ids = cluster_t2_instances_ids
        self.cluster_m4_instances_ids = cluster_m4_instances_ids

        print(f'ELB ID : {self.elb_id}')
        print(f'Cluster T2 ID : {self.cluster_t2_id}')
        print(f'Cluster M4 ID : {self.cluster_m4_id}')

        self.metrics_instances = ['CPUUtilization']

        # Correspondance between metric and the relevant stat [Average, Sum, Min, Max]
        self.metrics_stat = {
            'UnHealthyHostCount': 'Average',
            'HealthyHostCount': 'Average',
            'TargetResponseTime': 'Average',
            'RequestCount': 'Sum',
            'HTTPCode_Target_4XX_Count': 'Sum',
            'HTTPCode_Target_2XX_Count': 'Sum',
            'RequestCountPerTarget': 'Sum',
            'HTTPCode_ELB_5XX_Count': 'Sum',
            'HTTPCode_ELB_503_Count': 'Sum',
            'HTTPCode_Target_2XX_Count': 'Sum',
            'ActiveConnectionCount': 'Sum',
            'NewConnectionCount': 'Sum',
            'ProcessedBytes': 'Sum',
            'ConsumedLCUs': 'Sum'
        }


    def get_instances_metric_statistics(self, instance_id):
        """Retrieves statistics on EC2 instances based on metrics defined in metrics_instances. """

        for metric in self.metrics_instances:
            statistics = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName=metric,
                Dimensions= [
                    {
                        'Name': 'InstanceId',
                        'Value': instance_id
                    }
                ],
                StartTime=datetime.utcnow() - timedelta(minutes=60),
                EndTime=datetime.utcnow(),
                Period=60,
                Statistics=['Minimum', 'Maximum', 'Average']
            )

        return statistics


    def build_target_group_metric_queries(self, metric_queries, metrics):
        """Builds the queries to specify which target group metric data to retrieve. """
        for id, metric in enumerate(metrics):
            metric_queries.append({
                    'Id': f'metric_{id}',
                    'MetricStat': {
                        'Metric': metric,
                        'Period': 60,
                        'Stat': self.metrics_stat[metric['MetricName']]
                    }
                })
            
        return metric_queries


    def get_metric_data(self):
        """Retrieve data for all available metrics """
        # Get all metrics that contain elb_id
        metrics_ELB = [m for m in self.cloudwatch.list_metrics()['Metrics'] if any(True for dim in m['Dimensions'] if self.elb_id in dim.values())]

        # Get all metrics that contain cluster_t2_id
        metrics_T2 = [m for m in self.cloudwatch.list_metrics()['Metrics'] if any(True for dim in m['Dimensions'] if self.cluster_t2_id in dim.values())]

        # Get all metrics that contain cluster_m4_id
        metrics_M4 = [m for m in self.cloudwatch.list_metrics()['Metrics'] if any(True for dim in m['Dimensions'] if self.cluster_m4_id in dim.values())]

        # Combine metrics and remove duplicates
        metrics = metrics_ELB + metrics_T2 + metrics_M4
        metrics = [i for n, i in enumerate(metrics) if i not in metrics[n + 1:]]

        # Store the metrics retrieved above in a json file
        with open('json/list_metrics.json', 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=4)

        # Build the body of the queries
        metric_queries = []
        metric_queries = self.build_target_group_metric_queries(metric_queries, metrics)

        # Store the queries in a json file
        with open('json/metric_queries.json', 'w', encoding='utf-8') as f:
            json.dump(metric_queries, f, ensure_ascii=False, indent=4)

        # Retrieve data from CloudWatch
        response = self.cloudwatch.get_metric_data(
            MetricDataQueries=metric_queries,
            StartTime=datetime.utcnow() - timedelta(minutes=60),
            EndTime=datetime.utcnow()
        )

        # Store the CloudWatch data
        with open('json/response.json', 'w', encoding='utf-8') as f:
            json.dump(response, f, ensure_ascii=False, indent=4, default=str)

        data_cluster = response["MetricDataResults"]

        return data_cluster


    def generate_plots(self, data):
        """Create and export a plot for each metric using its datapoints."""

        plt.rcParams["figure.figsize"] = 12,5
        for metric in data:
            # Convert dictionary data into pandas
            df = pd.DataFrame.from_dict(metric)[["Timestamps","Values"]]

            if len(df) == 0:
                print(f"ERROR: No datapoints were found for metric {metric['Id']}")

            # Rename columns
            df.rename(columns={'Values': 'Cluster?'}, inplace=True)

            # Parse strings to datetime type
            df["Timestamps"] = pd.to_datetime(df["Timestamps"], infer_datetime_format=True)
            
            # Create plot
            if len(df)!=0:
                print(f"drawing plot {metric['Id']}")
                plt.figure()
                plt.xlabel("Timestamps")
                plt.plot("Timestamps", "Cluster?", color="red", data=df)
                plt.title(metric['Label'].split(' ')[-1])
                handles, labels = plt.gca().get_legend_handles_labels()
                by_label = dict(zip(labels, handles))
                plt.legend(by_label.values(), by_label.keys())
                plt.savefig(f"plots/{metric['Id']}")      
            

    def prepare_results(self):
        """Retrieve metrics and report the performance by generating plots and showing statistics."""

        print("retrieving metrics...")
        # Retrieve datapoints of each chosen metric collected from cluster t2
        data = self.get_metric_data()

        # Generate plots for clusters comparison
        self.generate_plots(data)

        # # Retrieve statistics of each chosen metric collected from ec2 instances of cluster t2
        for instance_id in self.cluster_t2_instances_ids:
            statistics = self.get_instances_metric_statistics(instance_id)

            print(f"CPU Utilization of instance {instance_id} in cluster t2")
            print(f"Minimum: {statistics['Datapoints'][0]['Minimum']}")
            print(f"Maximum: {statistics['Datapoints'][0]['Maximum']}")
            print(f"Average: {statistics['Datapoints'][0]['Average']}\n")

        
        # Retrieve statistics of each chosen metric collected from ec2 instances of cluster m4
        for instance_id in self.cluster_m4_instances_ids:
            statistics = self.get_instances_metric_statistics(instance_id)

            print(f"CPU Utilization of instance {instance_id} in cluster m4")
            print(f"Minimum: {statistics['Datapoints'][0]['Minimum']}")
            print(f"Maximum: {statistics['Datapoints'][0]['Maximum']}")
            print(f"Average: {statistics['Datapoints'][0]['Average']}\n")