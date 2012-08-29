# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

'''
Helper utilities related to the AWS API implementations
'''

import re
import itertools


def format_response(action, response):
    """
    Format response from engine into API format
    """
    return {'%sResponse' % action: {'%sResult' % action: response}}


def extract_param_pairs(params, prefix='', keyname='', valuename=''):
    """
    Extract a dictionary of user input parameters, from AWS style
    parameter-pair encoded list

    In the AWS API list items appear as two key-value
    pairs (passed as query parameters)  with keys of the form below:

    Prefix.member.1.keyname=somekey
    Prefix.member.1.keyvalue=somevalue
    Prefix.member.2.keyname=anotherkey
    Prefix.member.2.keyvalue=somevalue

    We reformat this into a dict here to match the heat
    engine API expected format
    """
    # Define the AWS key format to extract
    LIST_KEYS = (
    LIST_USER_KEY_re,
    LIST_USER_VALUE_fmt,
    ) = (
    re.compile(r"%s\.member\.(.*?)\.%s$" % (prefix, keyname)),
    '.'.join([prefix, 'member', '%s', valuename])
    )

    def get_param_pairs():
        for k in params:
            keymatch = LIST_USER_KEY_re.match(k)
            if keymatch:
                key = params[k]
                v = LIST_USER_VALUE_fmt % keymatch.group(1)
                try:
                    value = params[v]
                except KeyError:
                    logger.error('Could not extract parameter %s' % key)

                yield (key, value)

    return dict(get_param_pairs())


def extract_param_list(params, prefix=''):
    """
    Extract a list-of-dicts based on parameters containing AWS style list

    MetricData.member.1.MetricName=buffers
    MetricData.member.1.Unit=Bytes
    MetricData.member.1.Value=231434333
    MetricData.member.2.MetricName=buffers2
    MetricData.member.2.Unit=Bytes
    MetricData.member.2.Value=12345

    This can be extracted by passing prefix=MetricData, resulting in a
    list containing two dicts
    """

    key_re = re.compile(r"%s\.member\.([0-9]+)\.(.*)" % (prefix))

    def get_param_data(params):
        for param_name, value in params.items():
            match = key_re.match(param_name)
            if match:
                try:
                    index = int(match.group(1))
                except ValueError:
                    pass
                else:
                    key = match.group(2)

                    yield (index, (key, value))

    # Sort and group by index
    key_func = lambda d: d[0]
    data = sorted(get_param_data(params), key=key_func)
    members = itertools.groupby(data, key_func)

    return [dict(kv for di, kv in m) for mi, m in members]


def reformat_dict_keys(keymap={}, inputdict={}):
    '''
    Utility function for mapping one dict format to another
    '''
    result = {}
    for key in keymap:
        result[keymap[key]] = inputdict[key]
    return result