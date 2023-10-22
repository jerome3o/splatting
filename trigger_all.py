from pathlib import Path

from dagster_graphql import DagsterGraphQLClient


def main():
    client = DagsterGraphQLClient("localhost:3000")

    # get all folders in data/splat_inputs
    input_dirs = [str(p) for p in Path("data/splat_inputs").glob("*") if p.is_dir()]

    for p in input_dirs:
        client.submit_job_execution(
            "gaussian_splat_job",
            run_config={
                "resources": {
                    "gaussian_splat_config": {
                        "config": {
                            "input_dir": p,
                            "splatting_repo_dir": "gaussian-splatting",
                        }
                    }
                },
                "ops": {
                    "frames": {
                        "config": {
                            "frames_per_second": 6
                        }
                    }
                }
            }
        )


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    main()
