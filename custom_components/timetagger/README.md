# TimeTagger Integration for Home Assistant

A Home Assistant integration for [TimeTagger](https://timetagger.app), a time tracking application. This integration allows you to monitor your working hours and time tracking data directly in Home Assistant.

## Features

- Track daily, weekly, and monthly working hours
- Monitor remaining work time for the current week
- Calculate monthly working time balance (overtime)
- Configurable daily target hours
- Support for work tags filtering
- Automatic updates every 5 minutes

## Installation

### HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Ottes42&repository=hass-integrations&category=Integration)

1. Ensure you have [HACS](https://hacs.xyz/) installed
2. Add this repository as a custom repository in HACS
3. Install the TimeTagger integration
4. Restart Home Assistant

### Manual Installation

1. Copy the `timetagger` folder to your `custom_components` directory
2. Restart Home Assistant

## Configuration

The integration can be configured through the Home Assistant UI:

1. Go to **Configuration** → **Integrations**
2. Click **Add Integration**
3. Search for **TimeTagger**
4. Fill in the required information:
   - **API URL**: Your TimeTagger instance URL (e.g., `https://your-host/timetagger/`)
   - **API Token**: Your TimeTagger API token
   - **Work Tags**: Comma-separated list of tags to track (e.g., `#work,#home`)
   - **Daily Target Hours**: Your target working hours per day (default: 8.0)

### Getting Your API Token

1. Log into your TimeTagger instance
2. Go to **Settings** → **API Access**
3. Generate or copy your API token

## Entities

The integration provides the following sensor entities:

### Working Hours Today

- **Entity ID**: `sensor.timetagger_working_hours_today`
- **Unit**: hours (h)
- **Description**: Total working hours logged today

### Working Hours This Week

- **Entity ID**: `sensor.timetagger_working_hours_this_week`
- **Unit**: hours (h)
- **Description**: Total working hours logged this week (Monday to current day)

### Working Hours This Month

- **Entity ID**: `sensor.timetagger_working_hours_this_month`
- **Unit**: hours (h)
- **Description**: Total working hours logged this month

### Remaining Time This Week

- **Entity ID**: `sensor.timetagger_remaining_time_this_week`
- **Unit**: hours (h)
- **Description**: Remaining work time to reach weekly target
- **Attributes**:
  - `target_hours`: Target hours for the week based on weekdays passed
  - `worked_hours`: Actual hours worked this week

### Monthly Working Time Balance

- **Entity ID**: `sensor.timetagger_monthly_working_time_balance`
- **Unit**: hours (h)
- **Description**: Monthly balance showing overtime (positive) or negative
- **Attributes**:
  - `worked_hours`: Actual hours worked this month
  - `target_hours`: Target hours for the month based on weekdays passed

## Usage Examples

### Dashboard Card

```yaml
type: entities
title: Time Tracking
entities:
  - entity: sensor.timetagger_working_hours_today
    name: Today
  - entity: sensor.timetagger_working_hours_this_week
    name: This Week
  - entity: sensor.timetagger_remaining_time_this_week
    name: Remaining This Week
  - entity: sensor.timetagger_monthly_working_time_balance
    name: Monthly Balance
```

### Automation Example

```yaml
automation:
  - alias: "Notify when daily target reached"
    trigger:
      - platform: numeric_state
        entity_id: sensor.timetagger_working_hours_today
        above: 8.0
    action:
      - service: notify.mobile_app_your_device
        data:
          message: "🎉 Daily target reached! You've worked {{ states('sensor.timetagger_working_hours_today') }} hours today."
```

## Configuration Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `api_url` | string | Yes | - | TimeTagger API endpoint URL |
| `token` | string | Yes | - | TimeTagger API token |
| `work_tags` | string | No | `#work,#home` | Comma-separated list of tags to track |
| `daily_target` | float | No | `8.0` | Target working hours per day |

## Data Update

- The integration fetches data from TimeTagger every 5 minutes
- Only records with the specified work tags are included
- Time calculations exclude weekends for target calculations

## Troubleshooting

### Common Issues

1. **Invalid URL Error**
   - Ensure your API URL starts with `http://` or `https://`
   - Verify the URL is accessible from your Home Assistant instance

2. **Authentication Errors**
   - Check your API token is correct and hasn't expired
   - Ensure your TimeTagger instance is accessible

3. **No Data**
   - Verify your work tags match the tags used in TimeTagger
   - Check that you have time entries with the specified tags

### Debug Logging

To enable debug logging, add this to your `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.timetagger: debug
```

## Support

For issues and feature requests, please visit the [GitHub repository](https://github.com/Ottes42/hass-integrations/issues).

## License

This integration is released under the same license as Home Assistant.
