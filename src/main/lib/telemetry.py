from influxdb import InfluxDBClient


def _get_influx_client(db):
    host = '192.168.1.200'
    port = 8086
    return InfluxDBClient(host=host, port=port, database=db)


def send_data_lines(database, data_lines):
    """
    :param database: the database to publish to
    :param data_lines: array of data lines in the InfluxDB line format protocol
    """
    client = _get_influx_client(database)
    client.write(data_lines, {'db': database, 'precision': 's'}, protocol='line')


def to_data_line(metric, value, tags, timestamp=None):
    def escape(val):
        if not isinstance(val, str):
            return val
        return val.replace(' ', '\\ ').replace(',', '\\,')

    tags_string = ",".join(["%s=%s" % (t_key, escape(t_value)) for t_key, t_value in tags.items()])
    if len(tags_string) > 0:
        tags_string = ',' + tags_string
    point_line = "%s%s value=%s" % (metric, tags_string, value)
    if timestamp:
        point_line += " %s" % int(timestamp)

    return point_line


def send_data(database, data, tags={}, timestamp=None):
    """
    :param database: the database to publish to
    :param data: dict with key representing the metric name and value representing the data point value
    :param tags: dict with tags to be added to the data point
    :param timestamp: timestamp in seconds to be applied to the metric
    """

    data_points = []
    for metric, value in data.items():
        data_points.append(to_data_line(metric, value, tags, timestamp))

    send_data_lines(database, data_points)
