/** Champ de formulaire avec libellé et messages d'erreur renvoyés par l'API ({ champ: ['message'] }). */
export default function Field({ label, name, errors, required, help, as = 'input', ...props }) {
  const Tag = as
  const list = errors?.[name]
  return (
    <div className="field">
      <label htmlFor={name}>{label}{required && <span className="req"> *</span>}</label>
      <Tag id={name} name={name} className="input" required={required} aria-invalid={Boolean(list)} {...props} />
      {help && <div className="help">{help}</div>}
      {Array.isArray(list) && list.map((m) => <div className="err" key={m}>{m}</div>)}
    </div>
  )
}
