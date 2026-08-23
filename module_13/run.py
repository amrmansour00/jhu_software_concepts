"""Flask application for GradCafe analytics and admissions prediction."""

# pylint: disable=too-few-public-methods

from flask import Flask, jsonify, render_template, request

from query_data import clamp_limit, run_queries

# Keep the earlier Module 5 data-loading functionality if available.
try:
    from load_data import load_records
except ImportError:
    load_records = None

# Module 13 inference functions.
from inference import (
    load_model,
    create_applicant_text,
    predict,
)


class AppState:
    """Application state used to gate pull/update operations."""

    def __init__(self):
        self.busy = False


def format_results(raw_results):
    """Format SQL rows for display."""

    formatted = {}

    for question, rows in raw_results.items():
        answers = []

        for row in rows:
            if len(row) == 1:
                answers.append(
                    f"Answer: {row[0]}"
                )
            else:
                answers.append(
                    "Answer: "
                    + " | ".join(
                        str(item)
                        for item in row
                    )
                )

        formatted[question] = answers

    return formatted


def safe_text(value):
    """
    Convert missing or blank text input into the same
    'Unknown' placeholder used during model training.
    """

    if value is None:
        return "Unknown"

    cleaned = str(value).strip()

    if cleaned == "":
        return "Unknown"

    return cleaned


def safe_number(value, field_name):
    """
    Validate optional numeric input.

    Blank input is allowed and becomes 'Unknown'.
    Invalid numeric input produces a friendly validation error.
    """

    if value is None:
        return "Unknown"

    cleaned = str(value).strip()

    if cleaned == "":
        return "Unknown"

    try:
        number = float(cleaned)

    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a valid number "
            "or may be left blank."
        ) from exc

    if number.is_integer():
        return str(int(number))

    return str(number)


def create_app(
    query_function=None,
    loader_function=None,
    state=None,
):
    """Create and configure the Flask application."""

    app = Flask(__name__)

    app_state = state or AppState()

    query_function = (
        query_function
        or run_queries
    )

    # ---------------------------------------------------------
    # Existing Module 5 loader
    # ---------------------------------------------------------

    def default_loader():

        if load_records is None:
            raise RuntimeError(
                "The earlier Module 5 load_data.py file "
                "is not available in Module 13."
            )

        return load_records([])

    loader_function = (
        loader_function
        or default_loader
    )


    # =========================================================
    # LOAD DISTILBERT ONCE AT APPLICATION STARTUP
    # =========================================================
    #
    # The model is NOT retrained.
    # The model is NOT reloaded for every request.

    prediction_tokenizer = None
    prediction_model = None
    prediction_metadata = None
    model_load_error = None

    try:

        (
            prediction_tokenizer,
            prediction_model,
            prediction_metadata,
        ) = load_model()

        print(
            "\nFlask prediction model loaded successfully."
        )

    except Exception as error:

        model_load_error = str(error)

        print(
            "\nWARNING: Prediction model "
            "could not be loaded."
        )

        print(
            model_load_error
        )


    # =========================================================
    # EXISTING ANALYSIS PAGE
    # =========================================================

    @app.route("/")
    @app.route("/analysis")
    def analysis():
        """Display the earlier GradCafe analysis page."""

        limit = clamp_limit(
            request.args.get(
                "limit",
                10
            )
        )

        try:

            raw_results = query_function(
                limit=limit
            )

            results = format_results(
                raw_results
            )

        except Exception:

            # Keep the Flask website available even when the
            # earlier PostgreSQL database is not running.

            results = {
                "Analysis unavailable": [
                    (
                        "The earlier PostgreSQL analysis "
                        "is not currently available. "
                        "The Will You Get In? prediction "
                        "page can still be used."
                    )
                ]
            }

        return render_template(
            "index.html",
            results=results,
        )


    # =========================================================
    # SECTION 7
    # WILL YOU GET IN?
    # =========================================================

    @app.route(
        "/will-you-get-in",
        methods=[
            "GET",
            "POST"
        ]
    )
    def will_you_get_in():
        """
        Display the admissions-prediction form and,
        after submission, run inference using the saved
        fine-tuned DistilBERT model.
        """

        prediction_result = None
        error_message = None

        form_values = {}

        if request.method == "POST":

            form_values = (
                request.form.to_dict()
            )

            # ---------------------------------------------
            # Check model availability
            # ---------------------------------------------

            if model_load_error:

                error_message = (
                    "The trained admissions model could "
                    "not be loaded. Please verify the "
                    "saved model files."
                )

            else:

                try:

                    # -------------------------------------
                    # Text fields
                    # -------------------------------------

                    program = safe_text(
                        request.form.get(
                            "program_name"
                        )
                    )

                    university = safe_text(
                        request.form.get(
                            "university"
                        )
                    )

                    degree = safe_text(
                        request.form.get(
                            "degree"
                        )
                    )

                    citizenship = safe_text(
                        request.form.get(
                            "student_type"
                        )
                    )

                    term = safe_text(
                        request.form.get(
                            "start_term"
                        )
                    )


                    # -------------------------------------
                    # Numeric fields
                    # -------------------------------------

                    gpa = safe_number(
                        request.form.get(
                            "gpa"
                        ),
                        "GPA",
                    )

                    gre = safe_number(
                        request.form.get(
                            "gre_score"
                        ),
                        "GRE",
                    )

                    gre_v = safe_number(
                        request.form.get(
                            "gre_v_score"
                        ),
                        "GRE Verbal",
                    )

                    gre_aw = safe_number(
                        request.form.get(
                            "gre_aw"
                        ),
                        "GRE Analytical Writing",
                    )


                    # -------------------------------------
                    # Comments
                    # -------------------------------------
                    #
                    # Section 7 asks for a comments /
                    # applicant-statement field on the page.
                    #
                    # The training dataset's comments field
                    # contained no usable values, so comments
                    # were NOT part of the trained model.
                    #
                    # We therefore accept the form field but
                    # deliberately do not add it to the model
                    # input. This keeps inference identical
                    # to training.

                    _comments = safe_text(
                        request.form.get(
                            "comments"
                        )
                    )


                    # -------------------------------------
                    # Recreate EXACT training-time input
                    # -------------------------------------

                    applicant_text = (
                        create_applicant_text(
                            program=program,
                            university=university,
                            degree=degree,
                            citizenship=citizenship,
                            gpa=gpa,
                            gre=gre,
                            gre_v=gre_v,
                            gre_aw=gre_aw,
                            term=term,
                        )
                    )


                    # -------------------------------------
                    # Run inference
                    # -------------------------------------

                    prediction_result = predict(
                        applicant_text,
                        prediction_tokenizer,
                        prediction_model,
                        prediction_metadata,
                    )


                    # Save text for optional display/debugging.
                    prediction_result[
                        "model_input"
                    ] = applicant_text


                except ValueError as error:

                    # Friendly form validation message.
                    error_message = str(
                        error
                    )


                except Exception:

                    # Never expose an internal Python
                    # traceback to a website user.

                    error_message = (
                        "The prediction could not be "
                        "completed. Please check your "
                        "inputs and try again."
                    )


        return render_template(
            "will_you_get_in.html",

            prediction=prediction_result,

            error_message=error_message,

            form_values=form_values,

            model_available=(
                model_load_error is None
            ),
        )


    # =========================================================
    # EXISTING MODULE 5 ROUTES
    # =========================================================

    @app.route(
        "/pull-data",
        methods=["POST"]
    )
    def pull_data():
        """Pull new data using the earlier Module 5 workflow."""

        if app_state.busy:

            return jsonify(
                {
                    "ok": False,
                    "busy": True,
                    "message":
                        "A data pull is already running.",
                }
            ), 409


        app_state.busy = True


        try:

            load_result = (
                loader_function()
            )

        except RuntimeError as error:

            app_state.busy = False

            return jsonify(
                {
                    "ok": False,
                    "busy": False,
                    "message": str(error),
                }
            ), 500


        app_state.busy = False


        return jsonify(
            {
                "ok": True,
                "busy": False,
                "message":
                    "Pull Data completed successfully.",
                "result": load_result,
            }
        ), 200


    @app.route(
        "/update-analysis",
        methods=["POST"]
    )
    def update_analysis():
        """Refresh the earlier analysis page."""

        if app_state.busy:

            return jsonify(
                {
                    "ok": False,
                    "busy": True,
                    "message":
                        "Analysis cannot update while "
                        "data pull is running.",
                }
            ), 409


        return jsonify(
            {
                "ok": True,
                "busy": False,
                "message":
                    "Analysis updated successfully.",
            }
        ), 200


    return app


# =========================================================
# RUN FLASK
# =========================================================

if __name__ == "__main__":

    flask_app = create_app()

    # Debug is intentionally disabled so public-facing
    # requests cannot expose Flask/Python stack traces.
    #
    # It also prevents the development reloader from
    # loading the large DistilBERT model twice.

    flask_app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
    )