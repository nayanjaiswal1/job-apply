from __future__ import annotations

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from job_agent.config.loader import load_config

log = structlog.get_logger()


def build_scheduler(
    email_tool=None,
    application_repo=None,
    followup_repo=None,
    outreach_repo=None,
    llm=None,
    notifier=None,
) -> AsyncIOScheduler:
    _, app_config = load_config()
    sched = app_config.schedule
    scheduler = AsyncIOScheduler()

    # Job search — every N hours
    scheduler.add_job(
        _noop("job_search"),
        IntervalTrigger(hours=sched.job_search_interval_hours),
        id="job_search",
        replace_existing=True,
    )

    # LinkedIn post scraper
    scheduler.add_job(
        _noop("linkedin_posts"),
        IntervalTrigger(hours=sched.linkedin_post_interval_hours),
        id="linkedin_posts",
        replace_existing=True,
    )

    # Mail watcher
    scheduler.add_job(
        _noop("mail_watcher"),
        IntervalTrigger(minutes=sched.mail_watcher_interval_minutes),
        id="mail_watcher",
        replace_existing=True,
    )

    # Follow-up sequencer — daily at 09:00
    h, m = map(int, sched.followup_time.split(":"))
    scheduler.add_job(
        _noop("followup"),
        CronTrigger(hour=h, minute=m),
        id="followup",
        replace_existing=True,
    )

    # Stale application check (ghost rule) — daily at 08:00
    sh, sm = map(int, sched.stale_check_time.split(":"))
    scheduler.add_job(
        _noop("ghost_check"),
        CronTrigger(hour=sh, minute=sm),
        id="ghost_check",
        replace_existing=True,
    )

    # Company research cache cleanup — weekly Sunday 02:00
    scheduler.add_job(
        _noop("company_cleanup"),
        CronTrigger(day_of_week="sun", hour=2),
        id="company_cleanup",
        replace_existing=True,
    )

    log.info("scheduler_built", job_count=len(scheduler.get_jobs()))
    return scheduler


def _noop(name: str):
    async def job():
        log.info("scheduled_job_stub", job=name)
    job.__name__ = name
    return job
