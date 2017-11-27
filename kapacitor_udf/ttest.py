from kapacitor.udf.agent import Agent, Handler
from scipy import stats
import math
import kapacitor.udf.udf_pb2 as udf_pb2
import sys

class TTestHandler(Handler):
    """
    Keep a rolling window of historically normal data
    When a new window arrives use a two-sided t-test to determine
    if the new window is statistically significantly different.
    """
    def __init__(self, agent):
        self._agent = agent

        self._field = ''
        self._history = None

        self._batch = None

        self._alpha = 0.0

    def info(self):
        """
        Respond with which type of edges we want/provide and any options we have.
        """
        response = udf_pb2.Response()
        # We will consume batch edges aka windows of data.
        response.info.wants = udf_pb2.BATCH
        # We will produce single points of data aka stream.
        response.info.provides = udf_pb2.STREAM

        # Here we can define options for the UDF.
        # Define which field we should process
        response.info.options['field'].valueTypes.append(udf_pb2.STRING)

        # Since we will be computing a moving average let's make the size configurable.
        # Define an option 'size' that takes one integer argument.
        response.info.options['size'].valueTypes.append(udf_pb2.INT)

        # We need to know the alpha level so that we can ignore bad windows
        # Define an option 'alpha' that takes one double argument.
        response.info.options['alpha'].valueTypes.append(udf_pb2.DOUBLE)

        return response

    def init(self, init_req):
        """
        Given a list of options initialize this instance of the handler
        """
        success = True
        msg = ''
        size = 0
        for opt in init_req.options:
            if opt.name == 'field':
                self._field = opt.values[0].stringValue
            elif opt.name == 'size':
                size = opt.values[0].intValue
            elif opt.name == 'alpha':
                self._alpha = opt.values[0].doubleValue

        if size <= 1:
            success = False
            msg += ' must supply window size > 1'
        if self._field == '':
            success = False
            msg += ' must supply a field name'
        if self._alpha == 0:
            success = False
            msg += ' must supply an alpha value'

        # Initialize our historical window
        self._history = MovingStats(size)

        response = udf_pb2.Response()
        response.init.success = success
        response.init.error = msg[1:]

        return response

    def snapshot(self):
        response = udf_pb2.Response()
        response.snapshot.snapshot = ''
        return response

    def restore(self, restore_req):
        response = udf_pb2.Response()
        response.restore.success = False
        response.restore.error = 'not implemented'
        return response

    def begin_batch(self, begin_req):
        # create new window for batch
        self._batch = MovingStats(-1)

    def point(self, point):
        self._batch.update(point.fieldsDouble[self._field])

    def end_batch(self, batch_meta):
        pvalue = 1.0
        if self._history.n != 0:
            # Perform Welch's t test
            t, pvalue = stats.ttest_ind_from_stats(
                    self._history.mean, self._history.stddev(), self._history.n,
                    self._batch.mean, self._batch.stddev(), self._batch.n,
                    equal_var=False)


            # Send pvalue point back to Kapacitor
            response = udf_pb2.Response()
            response.point.time = batch_meta.tmax
            response.point.name = batch_meta.name
            response.point.group = batch_meta.group
            response.point.tags.update(batch_meta.tags)
            response.point.fieldsDouble["t"] = t
            response.point.fieldsDouble["pvalue"] = pvalue
            self._agent.write_response(response)
	else:
            response = udf_pb2.Response()
            response = udf_pb2.Response()
            response.point.time = batch_meta.tmax
            response.point.name = batch_meta.name
            response.point.group = batch_meta.group
            response.point.tags.update(batch_meta.tags)
            response.point.fieldsDouble["t"] = 0.1
            response.point.fieldsDouble["pvalue"] = 0.1
            self._agent.write_response(response)

        # Update historical stats with batch, but only if it was normal.
        if pvalue > self._alpha:
            for value in self._batch._window:
                self._history.update(value)


class MovingStats(object):
    """
    Calculate the moving mean and variance of a window.
    Uses Welford's Algorithm.
    """
    def __init__(self, size):
        """
        Create new MovingStats object.
        Size can be -1, infinite size or > 1 meaning static size
        """
        self.size = size
        if not (self.size == -1 or self.size > 1):
            raise Exception("size must be -1 or > 1")


        self._window = []
        self.n = 0.0
        self.mean = 0.0
        self._s = 0.0

    def stddev(self):
        """
        Return the standard deviation
        """
        if self.n == 1:
            return 0.0
        return math.sqrt(self._s / (self.n - 1))

    def update(self, value):

        # update stats for new value
        self.n += 1.0
        diff = (value - self.mean)
        self.mean += diff / self.n
        self._s += diff * (value - self.mean)

        if self.n == self.size + 1:
            # update stats for removing old value
            old = self._window.pop(0)
            oldM = (self.n * self.mean - old)/(self.n - 1)
            self._s -= (old - self.mean) * (old - oldM)
            self.mean = oldM
            self.n -= 1

        self._window.append(value)

if __name__ == '__main__':
    # Create an agent
    agent = Agent()

    # Create a handler and pass it an agent so it can write points
    h = TTestHandler(agent)

    # Set the handler on the agent
    agent.handler = h

    # Anything printed to STDERR from a UDF process gets captured into the Kapacitor logs.
    print >> sys.stderr, "Starting agent for TTestHandler"
    agent.start()
    agent.wait()
    print >> sys.stderr, "Agent finished"
