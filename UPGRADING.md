# Upgrade guide

## Migrating from 3.x to 4.x

### Updated minimum Python version
The minimum supported Python version is now 3.5. Older versions of Python are
now at
[end-of-life](https://docs.python.org/devguide/#status-of-python-branches).
Please upgrade.

### Removal of deprecated properties from 2.x

The properties deprecated in the 3.0.0 release have been removed. See the below
guide for migrating from 2.x to 3.x to remove use of `get_endpoint()` and
`use_ssl`.

### Remove unused utilities

* Removed `bugsnag.utils.ThreadLocals` as it has been superseded by the
  `contextvars` API
* Removed `bugsnag.utils.merge_dicts`
* Removed `bugsnag.send_sessions`

### Request environment configuration

`Configuration.send_environment` is now disabled by default. Set
`send_environment=True` in your configuration to enable it and send the full
request context as a part of each event.

### Configuration validation

* Setting unknown properties on `Configuration` via `configure(**kwargs)` is no
longer supported and will cause an error.
* `Configuration.get('{propname}')` is deprecated in favor of accessing
  configuration properties directly

  ```diff+py
  - config.get('release_stage')
  + config.release_stage
  ```

## Migrating from 2.x to 3.x

A few configuration properties were deprecated in the transition from 2.x to
3.x, but should be relatively easy to upgrade.

### Endpoint configuration

Previously, `use_ssl` was used in combination with `get_endpoint()` and
`endpoint` to determine the correct URL receive error reports. `use_ssl` and
`Configuration.get_endpoint()` have been deprecated in favor of including the
protocol in the `endpoint` configuration option.

Replace:

```python
# old way
config = Configuration()
config.use_ssl = True
config.endpoint = 'my.example.com'
```

With:

```python
config = Configuration()
config.endpoint = 'https://my.example.com'
```

### Using different API keys with log handlers

The `api_key` constructor argument has been deprecated in favor of using a
client to set the correct API key.

Replace:

```python
# old way
handler = BugsnagHandler(api_key='some key')
```

With:

```python
client = Client(api_key='some key')
handler = client.log_handler()
```
