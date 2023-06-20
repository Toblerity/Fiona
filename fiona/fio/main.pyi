def configure_logging(verbosity: int) -> None: ...


def main_group(
    ctx,
    verbose: bool,
    quiet: bool,
    aws_profile: str,
    aws_no_sign_requests: bool,
    aws_requester_pays: bool,
) -> None: ...
