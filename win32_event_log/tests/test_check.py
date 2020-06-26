# (C) Datadog, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import pytest
import win32evtlog

from . import common

pytestmark = [pytest.mark.integration]


def test_expected(aggregator, dd_run_check, new_check, instance, report_event):
    check = new_check(instance)
    report_event('message')
    dd_run_check(check)

    aggregator.assert_event(
        'message',
        alert_type='info',
        priority='normal',
        host=check.hostname,
        source_type_name=check.SOURCE_TYPE_NAME,
        aggregation_key=common.EVENT_SOURCE,
        msg_title='Application/{}'.format(common.EVENT_SOURCE),
        tags=[],
    )


@pytest.mark.parametrize(
    'event_type, level',
    [
        pytest.param(win32evtlog.EVENTLOG_INFORMATION_TYPE, 'info', id='INFORMATION_TYPE'),
        pytest.param(win32evtlog.EVENTLOG_WARNING_TYPE, 'warning', id='WARNING_TYPE'),
        pytest.param(win32evtlog.EVENTLOG_ERROR_TYPE, 'error', id='ERROR_TYPE'),
    ],
)
def test_levels(aggregator, dd_run_check, new_check, instance, report_event, event_type, level):
    check = new_check(instance)
    report_event('foo', event_type=event_type)
    dd_run_check(check)

    aggregator.assert_event('foo', alert_type=level)


def test_event_priority(aggregator, dd_run_check, new_check, instance, report_event):
    instance['event_priority'] = 'low'
    check = new_check(instance)
    report_event('foo')
    dd_run_check(check)

    aggregator.assert_event('foo', priority='low')


def test_event_id(aggregator, dd_run_check, new_check, instance, report_event):
    instance['tag_event_id'] = True
    check = new_check(instance)
    report_event('foo')
    dd_run_check(check)

    aggregator.assert_event('foo', tags=['event_id:{}'.format(common.EVENT_ID)])


def test_message_whitelist(aggregator, dd_run_check, new_check, instance, report_event):
    instance['message_whitelist'] = ['bar']
    check = new_check(instance)
    report_event('foo')
    report_event('bar')
    report_event('baz')
    dd_run_check(check)

    assert len(aggregator.events) == 1
    aggregator.assert_event('bar')


def test_message_blacklist(aggregator, dd_run_check, new_check, instance, report_event):
    instance['message_blacklist'] = ['bar']
    check = new_check(instance)
    report_event('foo')
    report_event('bar')
    report_event('baz')
    dd_run_check(check)

    assert len(aggregator.events) == 2
    aggregator.assert_event('foo')
    aggregator.assert_event('baz')


def test_message_blacklist_override(aggregator, dd_run_check, new_check, instance, report_event):
    instance['message_whitelist'] = ['bar']
    instance['message_blacklist'] = ['bar']
    check = new_check(instance)
    report_event('foo')
    report_event('bar')
    report_event('baz')
    dd_run_check(check)

    assert len(aggregator.events) == 0


def test_custom_query(aggregator, dd_run_check, new_check, instance, report_event):
    instance['query'] = "*[System[Provider[@Name='{}']] and System[(Level=1 or Level=2)]]".format(common.EVENT_SOURCE)
    check = new_check(instance)
    report_event('foo', level='error')
    report_event('bar')
    dd_run_check(check)

    assert len(aggregator.events) == 1
    aggregator.assert_event('foo')


def test_bookmark(aggregator, dd_run_check, new_check, instance, report_event):
    instance['start'] = 'oldest'
    check = new_check(instance)
    report_event('foo')
    report_event('bar')
    dd_run_check(check)

    assert len(aggregator.events) > 1
    aggregator.reset()

    check = new_check(instance)
    dd_run_check(check)

    assert len(aggregator.events) == 0

    report_event('foo')
    dd_run_check(check)

    assert len(aggregator.events) == 1
    aggregator.assert_event('foo')
