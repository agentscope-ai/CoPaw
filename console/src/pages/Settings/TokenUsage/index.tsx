import { useEffect, useState } from "react";
import { Button, Card, message } from "@agentscope-ai/design";
import { DatePicker } from "antd";
import { useTranslation } from "react-i18next";
import dayjs, { Dayjs } from "dayjs";
import api from "../../../api";
import type { TokenUsageSummary } from "../../../api/types/tokenUsage";
import styles from "./index.module.less";

function TokenUsagePage() {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<TokenUsageSummary | null>(null);
  const [startDate, setStartDate] = useState<Dayjs>(
    dayjs().subtract(30, "day"),
  );
  const [endDate, setEndDate] = useState<Dayjs>(dayjs());

  const fetchData = async () => {
    setLoading(true);
    try {
      const summary = await api.getTokenUsage({
        start_date: startDate.format("YYYY-MM-DD"),
        end_date: endDate.format("YYYY-MM-DD"),
      });
      setData(summary);
    } catch (e) {
      console.error("Failed to load token usage:", e);
      message.error(t("tokenUsage.loadFailed"));
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleDateChange = (dates: [Dayjs | null, Dayjs | null] | null) => {
    if (dates?.[0]) setStartDate(dates[0]);
    if (dates?.[1]) setEndDate(dates[1]);
  };

  const handleQuery = () => {
    fetchData();
  };

  const formatNumber = (n: number) =>
    n.toLocaleString(undefined, { maximumFractionDigits: 0 });

  if (loading && !data) {
    return (
      <div className={styles.page}>
        <h1 className={styles.title}>{t("tokenUsage.title")}</h1>
        <p className={styles.description}>{t("tokenUsage.description")}</p>
        <span className={styles.loading}>{t("common.loading")}</span>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>{t("tokenUsage.title")}</h1>
      <p className={styles.description}>{t("tokenUsage.description")}</p>

      <div className={styles.filters}>
        <DatePicker.RangePicker
          value={[startDate, endDate]}
          onChange={handleDateChange}
          className={styles.datePicker}
        />
        <Button type="primary" onClick={handleQuery} loading={loading}>
          {t("tokenUsage.refresh")}
        </Button>
      </div>

      {data && data.total_calls > 0 ? (
        <>
          <div className={styles.summaryCards}>
            <Card className={styles.card}>
              <div className={styles.cardValue}>
                {formatNumber(data.total_tokens)}
              </div>
              <div className={styles.cardLabel}>
                {t("tokenUsage.totalTokens")}
              </div>
            </Card>
            <Card className={styles.card}>
              <div className={styles.cardValue}>
                {formatNumber(data.total_calls)}
              </div>
              <div className={styles.cardLabel}>
                {t("tokenUsage.totalCalls")}
              </div>
            </Card>
            <Card className={styles.card}>
              <div className={styles.cardValue}>
                {formatNumber(data.total_prompt_tokens)}
              </div>
              <div className={styles.cardLabel}>
                {t("tokenUsage.promptTokens")}
              </div>
            </Card>
            <Card className={styles.card}>
              <div className={styles.cardValue}>
                {formatNumber(data.total_completion_tokens)}
              </div>
              <div className={styles.cardLabel}>
                {t("tokenUsage.completionTokens")}
              </div>
            </Card>
          </div>

          {Object.keys(data.by_model).length > 0 && (
            <Card className={styles.tableCard} title={t("tokenUsage.byModel")}>
              <div className={styles.tableWrapper}>
                <table className={styles.table}>
                  <thead>
                    <tr>
                      <th>{t("tokenUsage.model")}</th>
                      <th>{t("tokenUsage.promptTokens")}</th>
                      <th>{t("tokenUsage.completionTokens")}</th>
                      <th>{t("tokenUsage.totalTokens")}</th>
                      <th>{t("tokenUsage.totalCalls")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(data.by_model).map(([model, stats]) => (
                      <tr key={model}>
                        <td className={styles.modelCell}>{model}</td>
                        <td>{formatNumber(stats.prompt_tokens)}</td>
                        <td>{formatNumber(stats.completion_tokens)}</td>
                        <td>{formatNumber(stats.total_tokens)}</td>
                        <td>{formatNumber(stats.call_count)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {Object.keys(data.by_date).length > 0 && (
            <Card className={styles.tableCard} title={t("tokenUsage.byDate")}>
              <div className={styles.tableWrapper}>
                <table className={styles.table}>
                  <thead>
                    <tr>
                      <th>{t("tokenUsage.date")}</th>
                      <th>{t("tokenUsage.promptTokens")}</th>
                      <th>{t("tokenUsage.completionTokens")}</th>
                      <th>{t("tokenUsage.totalTokens")}</th>
                      <th>{t("tokenUsage.totalCalls")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(data.by_date).map(([dt, stats]) => (
                      <tr key={dt}>
                        <td className={styles.modelCell}>{dt}</td>
                        <td>{formatNumber(stats.prompt_tokens)}</td>
                        <td>{formatNumber(stats.completion_tokens)}</td>
                        <td>{formatNumber(stats.total_tokens)}</td>
                        <td>{formatNumber(stats.call_count)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </>
      ) : (
        <Card className={styles.emptyCard}>
          <p className={styles.emptyText}>{t("tokenUsage.noData")}</p>
        </Card>
      )}
    </div>
  );
}

export default TokenUsagePage;
