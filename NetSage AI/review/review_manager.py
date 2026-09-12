import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from database.database import SessionLocal
from database.models import ReviewLog


class ReviewManager:

    INDIA_TIMEZONE = ZoneInfo("Asia/Kolkata")

    @staticmethod
    def save_review(case_id, decision, notes=""):
        db = SessionLocal()

        try:
            created_at = datetime.utcnow()

            new_review = ReviewLog(
                case_id=case_id,
                decision=decision,
                notes=notes,
                created_at=created_at
            )

            db.add(new_review)
            db.commit()
            db.refresh(new_review)

            print(
                f"Review saved successfully | "
                f"Case: {case_id} | "
                f"Decision: {decision} | "
                f"Timestamp UTC: {created_at}"
            )

            return True

        except Exception as e:
            db.rollback()

            print(
                f"Error saving review to database: {e}"
            )

            return False

        finally:
            db.close()

    @staticmethod
    def format_timestamp(created_at):

        if not created_at:
            return None

        try:
            utc_time = created_at.replace(
                tzinfo=timezone.utc
            )

            india_time = utc_time.astimezone(
                ReviewManager.INDIA_TIMEZONE
            )

            return india_time.strftime(
                "%Y-%m-%d %H:%M:%S IST"
            )

        except Exception as e:
            print(
                f"Error formatting timestamp: {e}"
            )

            return None

    @staticmethod
    def get_all_reviews():

        db = SessionLocal()

        try:
            reviews = (
                db.query(ReviewLog)
                .order_by(
                    ReviewLog.created_at.desc()
                )
                .all()
            )

            review_data = []

            for r in reviews:

                timestamp = ReviewManager.format_timestamp(
                    r.created_at
                )

                review_data.append(
                    {
                        "id": r.id,

                        "case_id": r.case_id,

                        "decision": r.decision,

                        "notes": r.notes,

                        "created_at": (
                            r.created_at.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                            if r.created_at
                            else None
                        ),

                        "timestamp": timestamp
                    }
                )

            return review_data

        finally:
            db.close()

    @staticmethod
    def get_all_logs():

        return ReviewManager.get_all_reviews()

    @staticmethod
    def get_analytics_stats():
 
        db = SessionLocal()

        try:
            reviews = db.query(ReviewLog).all()

            total_reviews = len(reviews)

            if total_reviews == 0:
                return {
                    "total_reviews": 0,
                    "accepted": 0,
                    "edited": 0,
                    "rejected": 0,
                    "acceptance_rate": 0.0
                }

            accepted = sum(
                1
                for r in reviews
                if str(r.decision).strip().lower()
                == "accepted"
            )

            edited = sum(
                1
                for r in reviews
                if str(r.decision).strip().lower()
                == "edited"
            )

            rejected = sum(
                1
                for r in reviews
                if str(r.decision).strip().lower()
                == "rejected"
            )

            acceptance_rate = round(
                (accepted / total_reviews) * 100,
                1
            )

            return {
                "total_reviews": total_reviews,
                "accepted": accepted,
                "edited": edited,
                "rejected": rejected,
                "acceptance_rate": acceptance_rate
            }

        finally:
            db.close()

    @staticmethod
    def get_metrics():
        logs = ReviewManager.get_all_logs()

        total_reviews = len(logs)

        # No reviews yet
        if total_reviews == 0:
            return {
                "total_reviews": 0,

                "accepted_count": 0,

                "edited_count": 0,

                "rejected_count": 0,

                "acceptance_rate": "0.0%",

                "edited_rate": "0.0%",

                "rejection_rate": "0.0%"
            }

        accepted_count = sum(
            1
            for log in logs
            if str(
                log.get("decision", "")
            ).strip().lower()
            == "accepted"
        )

        edited_count = sum(
            1
            for log in logs
            if str(
                log.get("decision", "")
            ).strip().lower()
            == "edited"
        )

        rejected_count = sum(
            1
            for log in logs
            if str(
                log.get("decision", "")
            ).strip().lower()
            == "rejected"
        )
        
        acceptance_rate = (
            accepted_count / total_reviews
        ) * 100

        edited_rate = (
            edited_count / total_reviews
        ) * 100

        rejection_rate = (
            rejected_count / total_reviews
        ) * 100

        return {
            "total_reviews": total_reviews,

            "accepted_count": accepted_count,

            "edited_count": edited_count,

            "rejected_count": rejected_count,

            "acceptance_rate": (
                f"{acceptance_rate:.1f}%"
            ),

            "edited_rate": (
                f"{edited_rate:.1f}%"
            ),

            "rejection_rate": (
                f"{rejection_rate:.1f}%"
            )
        }