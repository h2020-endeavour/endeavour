from influxdb import InfluxDBClient
from collections import OrderedDict


# Queries related to ports of a single switch.
# Port related queries return the last value recorded in the database.


def port_query(field, client, interval, dp_name, port_name):
    query = (
        'SELECT non_negative_derivative(mean(\"value\"), 1s)'
        'FROM \"{3}\"'
        'WHERE \"port_name\" = \'{2}\' AND \"dp_name\" = \'{1}\' AND time > now() - {0}s '
        'GROUP BY time({0}s) fill(null)').format(
        interval, dp_name, port_name, field)
    result = client.query(query)
    print result
    gen = result[('port_bytes_in', None)]
    for v in gen:
        return v["non_negative_derivative"]

# Queries related to flows.
# This function returns an ordered dictionary to enable the addition of
# more fields to the WHERE clause.


def base_flow_query(field, interval, dp_name, cookie=None, table_id=0):
    query = OrderedDict()
    query["SELECT"] = 'SELECT non_negative_derivative(mean(\"value\"), 1s)'
    query["FROM"] = 'FROM \"{0}\"'.format(field)
    query["WHERE"] = 'WHERE \"dp_name\" = \'{0}\' AND \"table_id\" = \'{1}\' '.format(
        dp_name, table_id)
    if cookie is not None:
        query["WHERE"] += 'AND \"cookie\" = \'{0}\' '.format(cookie)

    query[
        "GROUP BY"] = 'AND time > now() - {0}s GROUP BY time({0}s) fill(null)'.format(interval)
    return query

# Creates a query from a dictionary of flow match fields
# The return value is a string that complements the WHERE clause of a query.


def match_fields_query(flow):
    return " ".join(['AND \"%s\" = \'%s\' ' % (key, value)
                     for (key, value) in flow.items()])


def flow_query(field,client,interval,dp_name,cookie=None,table_id=0, 
               flow=None):
    query_dict = base_flow_query(field, interval, dp_name, cookie, table_id)
    if flow is not None:
        query_dict["WHERE"] += match_fields_query(flow)
    query = ' '.join(['%s' % (value) for (key, value) in query_dict.items()])
    result = client.query(query)
    gen = result[(field, None)]
    for v in gen:
        return v["non_negative_derivative"]

# The  StatsCollector needs to receive 
# an InfluxDBClient object to perform queries.
# e.g:
#   INFLUXDB_DB = "sdx"
#   INFLUXDB_HOST = "localhost"
#   INFLUXDB_PORT = 8086
#   INFLUXDB_USER = ""
#   INFLUXDB_PASS = ""
#   client = InfluxDBClient(
#       host=INFLUXDB_HOST, port=INFLUXDB_PORT,
#       username=INFLUXDB_USER, password=INFLUXDB_PASS,
#       database=INFLUXDB_DB, timeout=10)
#   c = StatsCollector(client)

class StatsCollector(object):

    def __init__(self, client):
        self.client = client

    def port_bytes_in(self, interval, dp_name, port_name):
        return port_query("port_bytes_in", self.client, interval, dp_name,
            port_name)

    def port_bytes_out(self, interval, dp_name, port_name):
        return port_query("port_bytes_out", self.client, interval, dp_name,
            port_name)

    def port_dropped_in(self, interval, dp_name, port_name):
        return port_query("port_dropped_in", self.client, interval, dp_name,
            port_name)

    def port_dropped_out(self, interval, dp_name, port_name):
        return port_query("port_dropped_out", self.client, interval, dp_name,
            port_name)

    def port_errors_in(self, interval, dp_name, port_name):
        return port_query("port_errors_in", self.client, interval,dp_name,
            port_name)

    def port_packets_in(self, interval, dp_name, port_name):
        return port_query("port_packets_in", self.client, interval, dp_name,
            port_name)

    def port_packets_out(self, interval, dp_name, port_name):
        return port_query("port_packets_out", self.client, interval, dp_name,
            port_name)

    # Return the rate of a flow in bytes per second.
    def flow_bytes(self, interval, dp_name, cookie=None, table_id=0,
            flow=None):
        return flow_query("flow_byte_count", self.client, interval, dp_name,
            cookie, table_id, flow)

    # Return the rate of a flow in packets per second.
    def flow_packets(self, interval, dp_name, cookie=None, table_id=0,
            flow=None):
        return flow_query("flow_packet_count",self.client, interval, dp_name,
            cookie, table_id, flow)
