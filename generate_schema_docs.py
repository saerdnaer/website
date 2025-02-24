import collections
import json
import re
import sys
from typing import List


def visit_generic(name: str, data, nullable: bool, required: bool):
    print('<header>')
    full_type = data['type']
    if full_type == 'array':
        full_type += ' of %s' % data['items']['type']
    print('<h3>%s</h3><span class="type">(%s)</span>' % (name, full_type))
    if required:
        print('<span class="tag required">required</span>')
    if nullable:
        print('<span class="tag nullable">nullable</span>')
    print('</header>')
    print('<details class="togglable">')
    print('<summary>Details</summary>')
    print('<div>')
    if 'description' in data:
        print('<p>%s</p>' % data['description'])
    if 'enum' in data:
        print('<h4>Valid values</h4>')
        print('<p><code>%s</code></p>' % '</code> | <code>'.join(data['enum']))
    if 'examples' in data:
        print('<h4>Examples</h4>')
        print('<p>')
        print(', '.join('<samp>%s</samp>' % e for e in data['examples']))
        print('</p>')
    if 'minItems' in data:
        print('<h4>Minimum number of items</h4>')
        print('<p>%s</p>' % data['minItems'])


def visit_object(name, data):
    assert 'properties' in data
    print('<h4>Nested object properties</h4>')
    print('<ul class="group">')
    visit(data['properties'], data.get('required', []))
    print('</ul>')


def visit_array(name, data):
    assert 'items' in data
    items = data['items']
    print('<h4>Nested array items</h4>')
    if items['type'] == 'string':
        print('<span>string</span>')
        if 'enum' in items:
            print('<h5>Valid values</h5>')
            print('<p><code>%s</code></p>' % '</code> | <code>'.join(items['enum']))
    elif items['type'] == 'object':
        print('<ul class="group">')
        visit(items['properties'], items.get('required', []))
        print('</ul>')
    if 'contains' in data:
        print('<h4>Required item values</h4>')
        # Ensure that we can handle this schema logic
        keys = set(data['contains'].keys())
        if keys != {'const'}:
            raise ValueError('Unspported "contains" variant(s): {}'.format(keys - {'const'}))
        # Generate docs
        print('<p>The array must contain the value')
        print('<code>{}</code>.</p>'.format(data['contains']['const']))


def visit_string(name, data):
    pass


def visit_number(name, data):
    pass


def visit_boolean(name, data):
    pass


def visit(properties, required_fields: List[str]):
    for k, v in properties.items():
        print('<li><section class="item">')
        nullable = False
        a = isinstance(v['type'], list)
        b = len(v['type']) == 2
        c = 'null' in v['type']
        if a and b and c:
            nullable = True
            v['type'].remove('null')
            v['type'] = v['type'][0]
        visit_generic(k, v, nullable, k in required_fields)
        if v['type'] == 'object':
            visit_object(k, v)
        elif v['type'] == 'string':
            visit_string(k, v)
        elif v['type'] == 'array':
            visit_array(k, v)
        elif v['type'] == 'number':
            visit_number(k, v)
        elif v['type'] == 'boolean':
            visit_boolean(k, v)
        else:
            print('Non object: %s' % v['type'], file=sys.stderr)
            sys.exit(1)
        print('</div></details>')
        print('</section></li>')


def process_version(path):
    with open(path, 'r') as f:
        schema = json.loads(f.read(), object_pairs_hook=collections.OrderedDict)
    assert schema['type'] == 'object'
    version = re.search(r'schema\.spaceapi\.io\/(.*)\.json', schema['$id']).group(1)
    schema['properties']['api_compatibility']
    assert 'properties' in schema
    print('_model: page')
    print('---')
    print('title: Schema Documentation v{}'.format(version))
    print('---')
    print('body:')
    print()
    print('This specification lists a number of standardized keys and values. It\'s highly')
    print('recommended to stick to these fields and values.')
    print()
    print('The full specification in the form of [JSON Schema](http://json-schema.org/) files ')
    print('can be found in the [schema repository](https://github.com/SpaceApi/schema).')
    print()
    print('If you need other fields in addition to the ones specified here, and you think')
    print('that the fields could be of use to others too, please make a change request in')
    print('the [schema repository](https://github.com/SpaceApi/schema).')
    print()
    print('If you still need to use non-standard fields, you should prefix them with')
    print('`ext_` to make it clear the field is not part of the documented API. If you')
    print('don\'t use that prefix, the fields will still be ignored by client')
    print('implementations, but they may collide with fields that we might standardize in')
    print('the future.')
    print()
    print('Most types are not nullable. That means that they may not contain the value "null",')
    print('but they may be left away if they\'re not required.')
    print()
    print('<ul class="group apidocs">')
    visit(schema['properties'], schema.get('required', []))
    print('</ul>')
    print('---')
    print('_discoverable: yes')
    print('---')
    print('_slug: docs')


if len(sys.argv) != 2:
    print('Usage: {} <path/to/schema.json>'.format(sys.argv[0]))
    sys.exit(1)

process_version(sys.argv[1])
