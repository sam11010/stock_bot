from robocorp.tasks import task
from rsi_sma_crossover import run_stock_analysis
from email_sender import send_email_task

@task
def master_task():
    # Kör aktieanalysen först:
    run_stock_analysis()
    # När analysen är klar, skicka e-postmeddelandet:
    send_email_task()

if __name__ == "__main__":
    master_task()