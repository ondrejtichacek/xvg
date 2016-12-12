import re
import numpy as np
import pprint

def read_xvg(path, var_names=None, unpack=False):
    """
    Reads xvg file, returns data as an instance of numpy.ndarray. If var_names
    are specified, only the respective columns are included; the ndarray columns
    are in that case rearanged so that they match the var_names array.

    Args:
        path: file path (convertible to str)
        var_names: variable names to be loaded, order matters (array of strings)

    Returns:
        data: m x n array of n variables (numpy.ndarray)
    """

    # Initialize the xvg reader.
    f = XvgFile(path, var_names)

    data = f.data

    if unpack is True:
        data = np.transpose(data)

    return data


class XvgFile(object):

    def __init__(self, path, var_names):

        self._data = None
        self.var_names = var_names

        # Store file path.
        self.path = path

        # Read file header
        self.read_header()

        # Get variable info
        self.variable_info()

    @property
    def data(self):
        if self._data is None:
            self._data = self.load_data()

        return self._data

    @data.setter
    def data(self, data):
        self._data = data

    def load_data(self, **kwargs):
        """
        Loads data using the numpy.loadtxt.function
        """

        # If variable names are specified
        if self.var_names is not None:
            # For each v in var_names get its position (column number) inside the
            # full data array.
            try:
                indices = [self.variables.index(v) for v in self.var_names if v in self.variables]
            except ValueError as e:
                match = re.match("'(.*)' is not in list", str(e))
                if match:
                    raise ValueError("Variable '{}' was not found in the xvg file.")
                else:
                    raise

        else:
            # Read all columns
            indices = None

        ncols = len(np.fromstring(self.data0, sep=' '))

        if ncols == len(self.variables):
            return np.loadtxt(
                str(self.path),
                comments={'#', '@', '&'},
                skiprows=self.data0_index,
                usecols=indices,
                **kwargs)
        else:
            return self.twocolloader(indices)

    def twocolloader(self, indices):

        with open(str(self.path), 'r') as fi:

            variables = []

            # Read file line by line
            for i, ln in enumerate(fi):
                if ln.startswith('#'):
                    pass
                elif ln.startswith('@'):
                    match = re.match(r'@target\s+[Gg]?(\d*)\.?[Ss](\d+)', ln)
                    if match:
                        var_index = int(match.group(2))
                        var_x = []
                        var_y = []

                        if indices is None or var_index + 1 in indices:
                            pass_this_var = False
                        else:
                            pass_this_var = True

                elif ln.startswith('&'):

                    if not pass_this_var:
                        variables.append({
                            'index': var_index,
                            'x': var_x,
                            'y': var_y,
                        })

                    var_x = []
                    var_y = []
                else:
                    if not pass_this_var:
                        v = np.fromstring(ln, sep=' ')
                        var_x.append(v[0])
                        var_y.append(v[1])

        if indices is not None:
            var_ind = [v['index'] for v in variables]
            variable_array = []

            for i in indices:
                if i == 0:
                    variable_array.append(variables[0]['x'])
                else:
                    variable_array.append(variables[var_ind.index(i-1)]['y'])
        else:
            variable_array = [variables[0]['x']]
            for v in variables:
                variable_array.append(v['y'])

        m = len(variable_array[0])
        n = len(variable_array)

        data = np.empty((m,n))

        for i, v in enumerate(variable_array):
            data[:,i] = v

        return data

    def variable_info(self):
        """
        Construct the array 'variables' containing name of each variable.
        """

        # Init.
        variables = []

        # Loop over lines in plotdirectives.
        for ln in self.plotdirectives:

            # Delete fist character '@' and strip whitespace
            ln = ln[1:]
            ln = ln.strip()

            # Now try to match different regex on each line.
            # If the match is successfull, continue to next line.

            match = re.match(r'title\s*"(.*)"', ln)
            if match:
                self.title = match.group(1)
                continue

            match = re.match(r'xaxis\s+label\s*"(.*)"', ln)
            if match:
                self.xaxis = match.group(1)
                continue

            match = re.match(r'yaxis\s+label\s*"(.*)"', ln)
            if match:
                self.yaxis = match.group(1)
                continue

            # If none of the previous matches was successfull and the internal
            # xvg type is 1, don't waste any more time of this line.
            # if self.xvg_type == 1:
                # continue

            # But if it's an xvg file of an internal type 2, we neet to try one
            # more match.
            # elif self.xvg_type == 2:

            match = re.match(r's(\d+)\s+legend\s+"(.*)"', ln)
            if match:
                variables.append(
                    {'index': int(match.group(1)),
                     'description': match.group(2)})
            continue

        # Append the independent variable. Since it is always in the
        # first column, set its index to -1 (will be sorted later).
        variables.append(
            {'index': -1,
             'description': self.xaxis})

        # In the end, add the dependent variable.
        # if self.xvg_type == 1:
        if len(variables) == 1:
            variables.append(
                {'index': 0,
                 'description': self.yaxis})

        # Sort the variables according to their index, discard the index.
        var_ind_sorted = np.argsort([v['index'] for v in variables])
        variables = [variables[i]['description'] for i in var_ind_sorted]

        # # Do some consistency checking.
        # if not len(variables) == self.data.shape[1]:
        #
        #     msg = "Not all variables were found!"
        #         + "Expected {}, found {}: {}".format(
        #             self.data.shape[1], len(variables), variables)
        #         + str(self.path)
        #
        #     raise RuntimeError(msg)

        # Store the variables array.
        self.variables = variables

    @property
    def xvg_type(self):
        """
        Determines the type of the file.

        In type 1, there are only two data columns and therefore, their names
        have to be obtained using @xaxis and @yaxis labels.

        In type 2, there are multiple columns. First is the independent variable
        and tha later columns are dependent variables. Names of the dependent
        variables are obtained using @s0, @s1, legends.
        """

        ncols = len(np.fromstring(self.data0, sep=' '))

        if ncols < 2:
            raise ValueError(
                "Expected to find at least two data columns, found {}.".format(
                    self.data.shape))

        elif ncols == 2:
            return 1

        else:
            return 2

    def read_header(self, header_on_top=True):
        """
        Reads header of xvg file -- lines starting with #, @, or &.
        Creates two arrays named 'comments' and 'plotdirectives', that contain
        lines staring with # and @, respectively. '&' lines are not yet
        implemented. The function also determines the index of the first data
        line.
        """

        # Init arrays
        self.comments = []
        self.plotdirectives = []

        # Init first data line index
        self.data0_index = None

        with open(str(self.path), 'r') as fi:

            # Read file line by line
            for i, ln in enumerate(fi):

                # Append line to arrays depending on the first character.

                if ln.startswith("#"):
                    self.comments.append(ln)

                elif ln.startswith("@"):
                    self.plotdirectives.append(ln)

                elif ln.startswith("&"):
                    raise RuntimeError(
                        "Lines starting with '&' are not implemented yet. Sorry!")

                # Prevent empty (or whitespace-only) lines to be recognised as
                # data lines.
                elif ln.strip() == "":
                    pass

                # If none of the previous applies, the line contains data.
                else:

                    # If it is the first encountered data line, log the line and
                    # its index.
                    if self.data0_index is None:
                        self.data0_index = i
                        self.data0 = ln

                    # If we assume, that the header is only on top of the file,
                    # we can break the file-reading.
                    if header_on_top:
                        break
