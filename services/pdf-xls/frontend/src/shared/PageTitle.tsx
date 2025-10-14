import { Helmet } from "react-helmet-async";

type Props = { suffix?: string };
const BASE = "77-Popular Tools";

export default function PageTitle({ suffix }: Props) {
  const title = suffix ? `${BASE} ${suffix}` : BASE;
  return (
    <Helmet>
      <title>{title}</title>
    </Helmet>
  );
}