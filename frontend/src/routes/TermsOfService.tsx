import LegalDocument, { type LegalCopy } from "@/components/LegalDocument";

const providerEs = (
  <>
    El servicio es prestado por <strong>Leon Hecht</strong>, Riehlstraße 16C,
    14057 Berlín, Alemania. Contacto: {" "}
    <a className="underline" href="mailto:leon@encuentra.app">leon@encuentra.app</a>.
  </>
);

const providerEn = (
  <>
    The service is provided by <strong>Leon Hecht</strong>, Riehlstraße 16C,
    14057 Berlin, Germany. Contact: {" "}
    <a className="underline" href="mailto:leon@encuentra.app">leon@encuentra.app</a>.
  </>
);

const spanish: LegalCopy = {
  title: "Términos del servicio",
  summary:
    "Estos términos regulan el acceso y uso de Encuentra, un servicio beta gratuito de búsqueda e investigación jurídica asistida por inteligencia artificial.",
  updatedLabel: "Última actualización: 2 de agosto de 2026",
  sections: [
    {
      title: "Proveedor y aceptación",
      paragraphs: [
        providerEs,
        "Al crear una cuenta o utilizar Encuentra, aceptas estos términos. Si no estás de acuerdo, no utilices el servicio. Si utilizas Encuentra en nombre de una organización, declaras que tienes autoridad para vincularla a estos términos.",
      ],
    },
    {
      title: "Servicio beta gratuito",
      paragraphs: [
        "Encuentra se ofrece actualmente de forma gratuita y en fase beta. Sus funciones pueden estar incompletas, cambiar sin previo aviso o experimentar errores e interrupciones. No se ha implementado facturación y estos términos no crean obligación de pago.",
        "Podremos introducir planes de pago en el futuro, pero informaremos de sus condiciones y solicitaremos una aceptación separada antes de cobrarte.",
      ],
    },
    {
      title: "Requisitos de uso",
      bullets: [
        "Debes tener al menos 18 años.",
        "La información de tu cuenta debe ser exacta y debes proteger tus credenciales y dispositivos.",
        "Eres responsable de toda actividad realizada mediante tu cuenta, salvo que nos informes oportunamente de un acceso no autorizado.",
        "Debes cumplir las leyes aplicables y las obligaciones profesionales o de confidencialidad que te correspondan.",
      ],
    },
    {
      title: "Investigación, no asesoramiento jurídico",
      paragraphs: [
        "Encuentra ofrece herramientas de búsqueda, síntesis y conversación para apoyar la investigación. No es un despacho jurídico, no presta asesoramiento jurídico y su uso no crea una relación abogado-cliente ni otra relación fiduciaria.",
        "Los resultados pueden ser incompletos, desactualizados, incorrectos o generados por inteligencia artificial. Las citas también pueden contener errores. Debes revisar las fuentes originales, verificar la legislación y jurisprudencia vigentes y obtener asesoramiento profesional antes de tomar decisiones jurídicas o actuar en plazos procesales.",
      ],
    },
    {
      title: "Contenido del usuario",
      paragraphs: [
        "Conservas los derechos que tengas sobre documentos, mensajes, consultas y demás contenido que proporciones. Nos concedes una licencia limitada, no exclusiva y mundial para alojar, copiar, procesar, transmitir y mostrar ese contenido únicamente cuando sea necesario para prestar, proteger y mantener Encuentra.",
        "Encuentra no utiliza tus documentos subidos ni conversaciones para entrenar modelos propios. Para generar una respuesta, partes relevantes de tu contenido pueden transmitirse a los proveedores técnicos indicados en la Política de privacidad.",
      ],
      bullets: [
        "Solo puedes proporcionar contenido que tengas derecho a utilizar y tratar.",
        "No debes subir material ilícito, malicioso, engañoso o que vulnere derechos de terceros.",
        "Eres responsable de eliminar o proteger datos personales, secretos profesionales y otra información confidencial cuando sea necesario.",
        "No debes confiar en Encuentra como único repositorio o sistema de respaldo de documentos.",
      ],
    },
    {
      title: "Uso aceptable",
      bullets: [
        "No intentes acceder a cuentas, datos o sistemas sin autorización.",
        "No eludas medidas de seguridad, límites técnicos o controles de acceso.",
        "No introduzcas malware ni utilices el servicio para fraude, acoso, discriminación u otras actividades ilícitas.",
        "No sobrecargues, interfieras o dañes deliberadamente el servicio o su infraestructura.",
        "No utilices resultados para tomar decisiones automatizadas de alto impacto sobre otra persona sin revisión humana y una base jurídica adecuada.",
        "No presentes resultados generados como una fuente oficial o una declaración verificada de hechos sin comprobarlos.",
      ],
    },
    {
      title: "Proveedores externos e inteligencia artificial",
      paragraphs: [
        "Encuentra depende de servicios externos, incluidos Supabase, Google, OpenAI y Amazon Web Services/OpenSearch. Su disponibilidad y funcionamiento pueden afectar al servicio. El uso opcional de Google para iniciar sesión también está sujeto a las condiciones de Google.",
        "El contenido generado automáticamente no representa la opinión de Leon Hecht ni garantiza un resultado jurídico. Encuentra no controla ni responde por sitios, documentos o servicios externos enlazados.",
      ],
    },
    {
      title: "Propiedad intelectual de Encuentra",
      paragraphs: [
        "Salvo el contenido del usuario y los materiales de terceros, Encuentra y sus componentes, diseño, software, marcas y contenido propio pertenecen a Leon Hecht o a sus licenciantes. Estos términos solo te conceden un derecho personal, limitado, revocable, no exclusivo e intransferible para utilizar el servicio conforme a estos términos.",
        "Nada de estos términos limita los derechos que la legislación aplicable te conceda para analizar o interoperar con software cuando esos derechos no puedan excluirse contractualmente.",
      ],
    },
    {
      title: "Disponibilidad y cambios",
      paragraphs: [
        "No prometemos que el servicio estará disponible de forma ininterrumpida, que se conservará una función concreta ni que cualquier error será corregido. Podemos modificar, limitar, suspender o retirar funciones beta por motivos técnicos, de seguridad, legales u operativos.",
        "Cuando sea razonablemente posible, intentaremos avisar de cambios que afecten de forma sustancial a los usuarios.",
      ],
    },
    {
      title: "Suspensión, terminación y eliminación",
      paragraphs: [
        "Puedes dejar de usar Encuentra en cualquier momento y solicitar la eliminación de tu cuenta escribiendo a leon@encuentra.app. Podemos limitar o suspender una cuenta cuando sea razonablemente necesario para proteger el servicio, investigar un abuso, cumplir la ley o responder a un incumplimiento de estos términos.",
        "Tras la terminación, tu derecho a usar el servicio finaliza. El tratamiento y eliminación de datos se rige por la Política de privacidad; algunas disposiciones que por su naturaleza deban continuar seguirán vigentes, incluidas las relativas a propiedad intelectual, responsabilidad y ley aplicable.",
      ],
    },
    {
      title: "Garantías y responsabilidad",
      paragraphs: [
        "Encuentra se presta gratuitamente en fase beta y con el nivel de diligencia exigido por la legislación aplicable. No ofrecemos garantías adicionales sobre exactitud, idoneidad para un asunto concreto, exhaustividad o disponibilidad de resultados jurídicos o generados por IA.",
        "La responsabilidad de Leon Hecht es ilimitada en caso de dolo o negligencia grave, daño a la vida, el cuerpo o la salud, garantías expresas y responsabilidad obligatoria prevista por la ley. En caso de negligencia leve, solo existirá responsabilidad por incumplimiento de una obligación contractual esencial y se limitará al daño típico y razonablemente previsible. Las limitaciones anteriores no reducen derechos obligatorios de consumidores.",
      ],
    },
    {
      title: "Ley aplicable y jurisdicción",
      paragraphs: [
        "Estos términos se rigen por la legislación de la República Federal de Alemania, con exclusión de la Convención de las Naciones Unidas sobre los Contratos de Compraventa Internacional de Mercaderías. Si eres consumidor, esta elección no te priva de la protección de las normas imperativas de tu país de residencia habitual.",
        "Los tribunales de Berlín tendrán jurisdicción exclusiva únicamente cuando la ley permita pactarla, especialmente en relaciones con comerciantes o entidades de derecho público. Los consumidores podrán acudir a los tribunales competentes conforme a la legislación aplicable, incluidos, cuando corresponda, los de su lugar de residencia.",
      ],
    },
    {
      title: "Cambios, idioma y contacto",
      paragraphs: [
        "Podemos actualizar estos términos para reflejar cambios legales, técnicos o del servicio. Publicaremos la versión revisada y su fecha. Cuando un cambio sea sustancial, proporcionaremos un aviso razonable cuando sea posible.",
        "Las versiones en español e inglés buscan expresar las mismas condiciones. En caso de discrepancia, la versión inglesa será la versión de referencia en la medida permitida por la ley, sin limitar derechos obligatorios de consumidores.",
        <>Para preguntas sobre estos términos, escribe a <a className="underline" href="mailto:leon@encuentra.app">leon@encuentra.app</a>.</>,
      ],
    },
  ],
};

const english: LegalCopy = {
  title: "Terms of Service",
  summary:
    "These terms govern access to and use of Encuentra, a free beta AI-assisted legal search and research service.",
  updatedLabel: "Last updated: August 2, 2026",
  sections: [
    {
      title: "Provider and acceptance",
      paragraphs: [
        providerEn,
        "By creating an account or using Encuentra, you agree to these terms. If you do not agree, do not use the service. If you use Encuentra for an organization, you represent that you have authority to bind that organization to these terms.",
      ],
    },
    {
      title: "Free beta service",
      paragraphs: [
        "Encuentra is currently provided free of charge and in beta. Features may be incomplete, change without notice, or experience errors and interruptions. Billing has not been implemented, and these terms create no payment obligation.",
        "We may introduce paid plans in the future, but we will provide the applicable terms and request separate acceptance before charging you.",
      ],
    },
    {
      title: "Eligibility and account responsibilities",
      bullets: [
        "You must be at least 18 years old.",
        "Your account information must be accurate, and you must protect your credentials and devices.",
        "You are responsible for activity through your account unless you promptly notify us of unauthorized access.",
        "You must comply with applicable laws and any professional or confidentiality obligations that apply to you.",
      ],
    },
    {
      title: "Research, not legal advice",
      paragraphs: [
        "Encuentra provides search, synthesis and conversational tools to support research. It is not a law firm, does not provide legal advice, and its use does not create an attorney-client or other fiduciary relationship.",
        "Results may be incomplete, outdated, incorrect or AI-generated. Citations may also contain errors. You must review original sources, verify current law and case law, and obtain professional advice before making legal decisions or acting on procedural deadlines.",
      ],
    },
    {
      title: "User content",
      paragraphs: [
        "You retain your rights in documents, messages, queries and other content you provide. You grant us a limited, non-exclusive, worldwide license to host, copy, process, transmit and display that content only as needed to provide, protect and maintain Encuentra.",
        "Encuentra does not use your uploaded documents or chats to train its own models. To generate a response, relevant parts of your content may be transmitted to the technical providers identified in the Privacy Policy.",
      ],
      bullets: [
        "You may provide only content you have the right to use and process.",
        "You must not upload unlawful, malicious, deceptive or rights-infringing material.",
        "You are responsible for removing or protecting personal data, professional secrets and other confidential information where necessary.",
        "You must not rely on Encuentra as the sole repository or backup for documents.",
      ],
    },
    {
      title: "Acceptable use",
      bullets: [
        "Do not attempt to access accounts, data or systems without authorization.",
        "Do not bypass security measures, technical limits or access controls.",
        "Do not introduce malware or use the service for fraud, harassment, discrimination or other unlawful activity.",
        "Do not deliberately overload, interfere with or damage the service or its infrastructure.",
        "Do not use outputs to make high-impact automated decisions about another person without human review and an appropriate legal basis.",
        "Do not present generated results as an official source or verified statement of fact without checking them.",
      ],
    },
    {
      title: "Third-party providers and artificial intelligence",
      paragraphs: [
        "Encuentra depends on third-party services, including Supabase, Google, OpenAI and Amazon Web Services/OpenSearch. Their availability and operation may affect the service. Optional Google sign-in is also subject to Google's terms.",
        "Automatically generated content does not represent Leon Hecht's opinion and does not guarantee a legal outcome. Encuentra does not control or accept responsibility for linked third-party sites, documents or services.",
      ],
    },
    {
      title: "Encuentra intellectual property",
      paragraphs: [
        "Except for user content and third-party materials, Encuentra and its components, design, software, marks and original content belong to Leon Hecht or his licensors. These terms grant only a personal, limited, revocable, non-exclusive and non-transferable right to use the service in accordance with these terms.",
        "Nothing in these terms restricts rights under applicable law to analyze software or achieve interoperability where those rights cannot be excluded by contract.",
      ],
    },
    {
      title: "Availability and changes",
      paragraphs: [
        "We do not promise uninterrupted availability, continued support for a particular feature, or correction of every error. We may modify, limit, suspend or withdraw beta features for technical, security, legal or operational reasons.",
        "Where reasonably possible, we will try to give notice of changes that materially affect users.",
      ],
    },
    {
      title: "Suspension, termination and deletion",
      paragraphs: [
        "You may stop using Encuentra at any time and request account deletion by emailing leon@encuentra.app. We may restrict or suspend an account where reasonably necessary to protect the service, investigate abuse, comply with law or respond to a breach of these terms.",
        "Upon termination, your right to use the service ends. Data handling and deletion are governed by the Privacy Policy. Provisions that by their nature should continue will survive, including those concerning intellectual property, liability and governing law.",
      ],
    },
    {
      title: "Warranties and liability",
      paragraphs: [
        "Encuentra is provided free of charge in beta and with the standard of care required by applicable law. We provide no additional warranty regarding the accuracy, fitness for a particular matter, completeness or availability of legal or AI-generated results.",
        "Leon Hecht's liability is unlimited for intent or gross negligence, injury to life, body or health, express guarantees, and liability that cannot legally be limited. For ordinary negligence, liability exists only for breach of an essential contractual obligation and is limited to typical, reasonably foreseeable loss. These limitations do not reduce mandatory consumer rights.",
      ],
    },
    {
      title: "Governing law and jurisdiction",
      paragraphs: [
        "These terms are governed by the laws of the Federal Republic of Germany, excluding the United Nations Convention on Contracts for the International Sale of Goods. If you are a consumer, this choice does not deprive you of mandatory protections under the law of your country of habitual residence.",
        "The courts of Berlin have exclusive jurisdiction only where such an agreement is legally permitted, particularly for merchants or public-law entities. Consumers may bring proceedings in any court available under applicable law, including, where applicable, the courts where they live.",
      ],
    },
    {
      title: "Changes, language and contact",
      paragraphs: [
        "We may update these terms to reflect legal, technical or service changes. We will post the revised version and effective date. Where a change is material, we will provide reasonable notice when possible.",
        "The Spanish and English versions are intended to express the same terms. If they differ, the English version is the reference version to the extent permitted by law, without limiting mandatory consumer rights.",
        <>For questions about these terms, email <a className="underline" href="mailto:leon@encuentra.app">leon@encuentra.app</a>.</>,
      ],
    },
  ],
};

export default function TermsOfService() {
  return <LegalDocument spanish={spanish} english={english} />;
}
