import LegalDocument, { type LegalCopy } from "@/components/LegalDocument";

const controllerEs = (
  <>
    <strong>Leon Hecht</strong><br />
    Riehlstraße 16C, 14057 Berlín, Alemania<br />
    Correo: <a className="underline" href="mailto:leon@encuentra.app">leon@encuentra.app</a>
  </>
);

const controllerEn = (
  <>
    <strong>Leon Hecht</strong><br />
    Riehlstraße 16C, 14057 Berlin, Germany<br />
    Email: <a className="underline" href="mailto:leon@encuentra.app">leon@encuentra.app</a>
  </>
);

const spanish: LegalCopy = {
  title: "Política de privacidad",
  summary:
    "Esta política explica cómo Encuentra trata los datos personales al prestar su servicio beta de búsqueda e investigación jurídica asistida por inteligencia artificial.",
  updatedLabel: "Última actualización: 2 de agosto de 2026",
  sections: [
    {
      title: "Responsable del tratamiento",
      paragraphs: [controllerEs],
    },
    {
      title: "Ámbito de esta política",
      paragraphs: [
        "Esta política se aplica al sitio web y a la aplicación Encuentra. Leon Hecht opera Encuentra a título personal como un servicio beta gratuito. No se ha designado un delegado de protección de datos porque actualmente no existe obligación legal de hacerlo.",
      ],
    },
    {
      title: "Datos que tratamos",
      bullets: [
        <><strong>Cuenta e identidad:</strong> nombre, correo electrónico, imagen de perfil, identificadores del proveedor de acceso y datos de autenticación. Si accedes con Google, recibimos de Google los datos de perfil que autorizas.</>,
        <><strong>Contenido del servicio:</strong> consultas de búsqueda, conversaciones, mensajes, comentarios, espacios de trabajo, documentos que subes y metadatos asociados.</>,
        <><strong>Datos técnicos y de seguridad:</strong> dirección IP, tipo de navegador o dispositivo, marcas de tiempo, registros de solicitudes, errores y eventos de seguridad.</>,
        <><strong>Datos almacenados en tu dispositivo:</strong> sesión de autenticación, preferencias esenciales de interfaz y referencias de documentos seleccionados mediante cookies o almacenamiento local.</>,
      ],
      paragraphs: [
        "No solicitamos deliberadamente categorías especiales de datos personales. Los documentos jurídicos pueden contener datos personales o confidenciales de terceros. Solo debes subirlos si tienes una base jurídica y autorización adecuadas para hacerlo.",
      ],
    },
    {
      title: "Finalidades y bases jurídicas",
      bullets: [
        <>Crear y gestionar tu cuenta, autenticarte y prestar las funciones solicitadas: ejecución del contrato o medidas precontractuales (art. 6.1.b del RGPD).</>,
        <>Procesar búsquedas, documentos y conversaciones para producir resultados y respuestas: ejecución del contrato (art. 6.1.b del RGPD).</>,
        <>Proteger, mantener, depurar y prevenir el uso indebido del servicio: interés legítimo en operar un servicio seguro y fiable (art. 6.1.f del RGPD).</>,
        <>Analizar comentarios agregados y métricas operativas para mejorar Encuentra: interés legítimo en mejorar el servicio (art. 6.1.f del RGPD).</>,
        <>Cumplir obligaciones legales y responder a solicitudes válidas de autoridades: obligación legal (art. 6.1.c del RGPD).</>,
        <>Realizar cualquier tratamiento opcional que solicite consentimiento: consentimiento (art. 6.1.a del RGPD), que podrás retirar en cualquier momento.</>,
      ],
      paragraphs: [
        "No vendemos datos personales ni los compartimos para publicidad dirigida. Actualmente no utilizamos herramientas de analítica publicitaria o de comportamiento.",
      ],
    },
    {
      title: "Inteligencia artificial",
      paragraphs: [
        "Para generar respuestas, Encuentra puede enviar a la API de OpenAI tus instrucciones, partes relevantes del historial de conversación y fragmentos de documentos recuperados o seleccionados. OpenAI procesa estos datos para prestar el servicio de API. Encuentra no utiliza tus conversaciones ni documentos subidos para entrenar modelos propios y no ha optado por compartir datos de la API de OpenAI para entrenar sus modelos.",
        "Las respuestas automatizadas son material de investigación y no constituyen asesoramiento jurídico ni decisiones con efectos legales. Evita introducir secretos, datos especialmente sensibles o información de terceros salvo que estés autorizado para hacerlo.",
      ],
    },
    {
      title: "Proveedores y destinatarios",
      bullets: [
        <><strong>Supabase:</strong> autenticación, gestión de cuentas, base de datos y servicios relacionados.</>,
        <><strong>Google:</strong> autenticación opcional mediante “Acceder con Google”. Google trata información conforme a su propia política cuando eliges este método.</>,
        <><strong>OpenAI:</strong> generación de respuestas mediante su API.</>,
        <><strong>Amazon Web Services y OpenSearch:</strong> alojamiento, almacenamiento, búsqueda e infraestructura técnica.</>,
        <>Asesores, proveedores técnicos adicionales o autoridades públicas, únicamente cuando sea necesario para operar el servicio, proteger derechos o cumplir la ley.</>,
      ],
      paragraphs: [
        "Encuentra no procesa actualmente pagos ni recopila datos de tarjetas. Esta política se actualizará antes de activar funciones de pago.",
      ],
    },
    {
      title: "Transferencias internacionales",
      paragraphs: [
        "Algunos proveedores pueden tratar datos fuera del Espacio Económico Europeo, incluido Estados Unidos. Cuando corresponde, estas transferencias se amparan en una decisión de adecuación, el Marco de Privacidad de Datos UE–EE. UU. o las cláusulas contractuales tipo de la Comisión Europea, junto con medidas adicionales apropiadas.",
      ],
    },
    {
      title: "Conservación",
      bullets: [
        <>Los datos de cuenta y el contenido del usuario se conservan mientras la cuenta esté activa o sean necesarios para prestar el servicio.</>,
        <>Tras una solicitud válida de eliminación, los datos activos se eliminan o anonimizan dentro de un plazo razonable. Las copias residuales pueden permanecer temporalmente en respaldos y registros de seguridad hasta su rotación.</>,
        <>Los registros pueden conservarse por más tiempo cuando sea necesario para seguridad, prevención de abusos, resolución de controversias o cumplimiento legal.</>,
        <>Los comentarios agregados o anonimizados pueden conservarse cuando ya no permitan identificar a una persona.</>,
      ],
    },
    {
      title: "Cookies y almacenamiento local",
      paragraphs: [
        "Encuentra utiliza únicamente tecnologías necesarias para mantener la sesión, recordar ajustes esenciales de interfaz y conservar referencias de documentos seleccionados. Son necesarias para prestar funciones expresamente solicitadas. No utilizamos cookies publicitarias ni de seguimiento entre sitios.",
      ],
    },
    {
      title: "Tus derechos",
      paragraphs: [
        <>Conforme al RGPD, puedes solicitar acceso, rectificación, eliminación, limitación, portabilidad y, cuando corresponda, oponerte al tratamiento o retirar tu consentimiento. Envía tu solicitud a <a className="underline" href="mailto:leon@encuentra.app">leon@encuentra.app</a>. Podemos pedir información razonable para verificar tu identidad.</>,
        <>También puedes presentar una reclamación ante la <a className="underline" href="https://www.datenschutz-berlin.de/" target="_blank" rel="noreferrer">Comisionada de Berlín para la Protección de Datos y la Libertad de Información</a>, o ante la autoridad de protección de datos de tu lugar de residencia.</>,
      ],
    },
    {
      title: "Seguridad",
      paragraphs: [
        "Aplicamos medidas técnicas y organizativas razonables para proteger los datos. Ningún sistema conectado a Internet es completamente seguro, por lo que no podemos garantizar seguridad absoluta. Si crees que tu cuenta o tus datos han sido comprometidos, contáctanos inmediatamente.",
      ],
    },
    {
      title: "Menores",
      paragraphs: [
        "Encuentra está dirigido a personas de 18 años o más. No recopilamos deliberadamente datos de menores de 18 años. Si detectamos que se han proporcionado dichos datos, tomaremos medidas razonables para eliminarlos.",
      ],
    },
    {
      title: "Cambios y contacto",
      paragraphs: [
        <>Podemos actualizar esta política cuando cambie el servicio o la normativa. Publicaremos la versión revisada y su fecha de entrada en vigor en esta página. Para preguntas o solicitudes de privacidad, escribe a <a className="underline" href="mailto:leon@encuentra.app">leon@encuentra.app</a>.</>,
      ],
    },
  ],
};

const english: LegalCopy = {
  title: "Privacy Policy",
  summary:
    "This policy explains how Encuentra handles personal data while providing its beta AI-assisted legal search and research service.",
  updatedLabel: "Last updated: August 2, 2026",
  sections: [
    {
      title: "Controller",
      paragraphs: [controllerEn],
    },
    {
      title: "Scope of this policy",
      paragraphs: [
        "This policy applies to the Encuentra website and application. Leon Hecht operates Encuentra personally as a free beta service. No data protection officer has been appointed because there is currently no legal obligation to appoint one.",
      ],
    },
    {
      title: "Data we process",
      bullets: [
        <><strong>Account and identity data:</strong> name, email address, profile image, sign-in provider identifiers and authentication data. If you sign in with Google, we receive the profile data you authorize Google to provide.</>,
        <><strong>Service content:</strong> search queries, conversations, messages, feedback, workspaces, documents you upload and associated metadata.</>,
        <><strong>Technical and security data:</strong> IP address, browser or device type, timestamps, request logs, errors and security events.</>,
        <><strong>Data on your device:</strong> authentication session, essential interface preferences and selected-document references stored through cookies or local storage.</>,
      ],
      paragraphs: [
        "We do not intentionally request special categories of personal data. Legal documents may contain personal or confidential information about third parties. You should upload such material only if you have an appropriate legal basis and authority to do so.",
      ],
    },
    {
      title: "Purposes and legal bases",
      bullets: [
        <>Creating and managing your account, authenticating you and providing requested features: performance of a contract or pre-contractual steps (GDPR Art. 6(1)(b)).</>,
        <>Processing searches, documents and conversations to produce results and responses: performance of a contract (GDPR Art. 6(1)(b)).</>,
        <>Protecting, maintaining and debugging the service and preventing misuse: our legitimate interest in operating a secure and reliable service (GDPR Art. 6(1)(f)).</>,
        <>Using aggregated feedback and operational metrics to improve Encuentra: our legitimate interest in improving the service (GDPR Art. 6(1)(f)).</>,
        <>Complying with legal obligations and valid authority requests: legal obligation (GDPR Art. 6(1)(c)).</>,
        <>Any optional processing for which consent is requested: consent (GDPR Art. 6(1)(a)), which you may withdraw at any time.</>,
      ],
      paragraphs: [
        "We do not sell personal data or share it for targeted advertising. We currently use no advertising or behavioural analytics tools.",
      ],
    },
    {
      title: "Artificial intelligence",
      paragraphs: [
        "To generate responses, Encuentra may send your instructions, relevant conversation history, and excerpts from retrieved or selected documents to the OpenAI API. OpenAI processes that information to provide the API service. Encuentra does not use your chats or uploaded documents to train its own models and has not opted in to sharing OpenAI API data for model training.",
        "Automated responses are research material and are not legal advice or decisions producing legal effects. Do not enter secrets, highly sensitive information or third-party information unless you are authorized to do so.",
      ],
    },
    {
      title: "Providers and recipients",
      bullets: [
        <><strong>Supabase:</strong> authentication, account management, database and related services.</>,
        <><strong>Google:</strong> optional “Sign in with Google” authentication. Google handles information under its own policies when you choose this method.</>,
        <><strong>OpenAI:</strong> response generation through its API.</>,
        <><strong>Amazon Web Services and OpenSearch:</strong> hosting, storage, search and technical infrastructure.</>,
        <>Advisers, additional technical providers or public authorities, only where necessary to operate the service, protect rights or comply with law.</>,
      ],
      paragraphs: [
        "Encuentra does not currently process payments or collect payment-card details. We will update this policy before enabling paid features.",
      ],
    },
    {
      title: "International transfers",
      paragraphs: [
        "Some providers may process data outside the European Economic Area, including in the United States. Where required, these transfers rely on an adequacy decision, the EU–U.S. Data Privacy Framework or European Commission Standard Contractual Clauses, together with appropriate supplementary measures.",
      ],
    },
    {
      title: "Retention",
      bullets: [
        <>Account data and user content are kept while the account is active or as needed to provide the service.</>,
        <>Following a valid deletion request, active data is deleted or anonymized within a reasonable operational period. Residual copies may remain temporarily in backups and security logs until they rotate.</>,
        <>Records may be kept longer where needed for security, abuse prevention, dispute resolution or legal compliance.</>,
        <>Aggregated or anonymized feedback may be retained where it can no longer identify an individual.</>,
      ],
    },
    {
      title: "Cookies and local storage",
      paragraphs: [
        "Encuentra uses only technologies needed to maintain your session, remember essential interface settings and retain references to selected documents. They are necessary to provide features you expressly request. We use no advertising or cross-site tracking cookies.",
      ],
    },
    {
      title: "Your rights",
      paragraphs: [
        <>Under the GDPR, you may request access, correction, deletion, restriction and portability, and, where applicable, object to processing or withdraw consent. Send requests to <a className="underline" href="mailto:leon@encuentra.app">leon@encuentra.app</a>. We may request reasonable information to verify your identity.</>,
        <>You may also complain to the <a className="underline" href="https://www.datenschutz-berlin.de/" target="_blank" rel="noreferrer">Berlin Commissioner for Data Protection and Freedom of Information</a>, or to the data protection authority where you live.</>,
      ],
    },
    {
      title: "Security",
      paragraphs: [
        "We use reasonable technical and organizational measures to protect data. No internet-connected system is completely secure, so absolute security cannot be guaranteed. Contact us immediately if you believe your account or data has been compromised.",
      ],
    },
    {
      title: "Children",
      paragraphs: [
        "Encuentra is intended for people aged 18 or older. We do not knowingly collect data from anyone under 18. If we learn that such data was provided, we will take reasonable steps to delete it.",
      ],
    },
    {
      title: "Changes and contact",
      paragraphs: [
        <>We may update this policy when the service or applicable law changes. The revised version and effective date will be posted here. For privacy questions or requests, email <a className="underline" href="mailto:leon@encuentra.app">leon@encuentra.app</a>.</>,
      ],
    },
  ],
};

export default function PrivacyPolicy() {
  return <LegalDocument spanish={spanish} english={english} />;
}
