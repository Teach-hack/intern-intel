"""Message builder for internship notifications."""

from __future__ import annotations

from app.models.internship import Internship

__all__ = ["MessageBuilder"]


class MessageBuilder:
    """Builds and formats notification messages for internships."""

    def _build_raw(self, job: Internship) -> str:
        """Construct the raw formatted message for a single internship without truncation."""
        parts = []
        parts.append("🚀 New Internship")

        company = job.company.strip() if job.company else "Unknown"
        parts.append(f"Company: {company}")

        title = job.title.strip() if job.title else "Unknown"
        parts.append(f"Title: {title}")

        if job.location and job.location.strip():
            parts.append(f"Location: {job.location.strip()}")

        emp_type = job.employment_type.strip() if job.employment_type else ""
        if emp_type:
            parts.append(f"Type: {emp_type.title()}")

        if job.posted_date:
            parts.append(f"Posted: {job.posted_date.isoformat()}")

        url = job.url.strip() if job.url else ""
        parts.append(f"Apply:\n{url}")

        return "\n\n".join(parts)

    def _truncate(self, text: str, max_length: int = 4000) -> str:
        """Truncate a string to max_length safely, preserving word boundaries if possible."""
        if len(text) <= max_length:
            return text

        limit = max_length - 3
        lookback = 50
        truncated_part = text[:limit]

        # Look back from the limit for a whitespace character to split cleanly
        for i in range(
            len(truncated_part) - 1, max(0, len(truncated_part) - lookback), -1
        ):
            if truncated_part[i].isspace():
                return truncated_part[:i].rstrip() + "..."

        # Fallback to hard character truncation if no whitespace is found within lookback
        return truncated_part + "..."

    def build(self, job: Internship) -> str:
        """Format a single internship listing into a notification message.

        Args:
            job: The internship listing database model instance.

        Returns:
            The formatted message, truncated if it exceeds 4000 characters.
        """
        return self._truncate(self._build_raw(job))

    def build_many(self, jobs: list[Internship]) -> str:
        """Format multiple internship listings into a single notification message.

        Args:
            jobs: A list of internship listings.

        Returns:
            A single combined notification message with listings separated by a divider,
            truncated if it exceeds 4000 characters.
        """
        if not jobs:
            return ""

        raw_messages = [self._build_raw(job) for job in jobs]
        combined = "\n\n---------------------\n\n".join(raw_messages)
        return self._truncate(combined)
